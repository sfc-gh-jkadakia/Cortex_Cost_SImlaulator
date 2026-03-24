"""
Snowflake Connection Helper
===========================
Utilities for connecting to Snowflake and running queries
to fetch actual usage data from ACCOUNT_USAGE views.
"""

import streamlit as st
import pandas as pd
from datetime import timedelta
from typing import Optional


def get_connection():
    """
    Get Snowflake connection using st.connection.
    Returns None if connection is not configured.
    """
    try:
        return st.connection("snowflake")
    except Exception as e:
        st.warning(f"Snowflake connection not configured: {e}")
        return None


def run_query(query: str, ttl: int = 600) -> Optional[pd.DataFrame]:
    """
    Run a query against Snowflake with caching.
    
    Args:
        query: SQL query to execute
        ttl: Cache time-to-live in seconds (default 10 minutes)
    
    Returns:
        DataFrame with results, or None if connection fails
    """
    conn = get_connection()
    if conn is None:
        return None
    
    try:
        return conn.query(query, ttl=timedelta(seconds=ttl))
    except Exception as e:
        st.error(f"Query failed: {e}")
        return None


# ============================================
# ACCOUNT_USAGE Queries for Cost Monitoring
# ============================================

def get_ai_services_daily_usage(days: int = 30) -> Optional[pd.DataFrame]:
    """
    Get daily AI services usage from METERING_DAILY_HISTORY.
    """
    query = f"""
    SELECT 
        USAGE_DATE,
        SERVICE_TYPE,
        CREDITS_USED,
        CREDITS_USED_COMPUTE,
        CREDITS_USED_CLOUD_SERVICES
    FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY
    WHERE SERVICE_TYPE = 'AI_SERVICES'
      AND USAGE_DATE >= DATEADD(day, -{days}, CURRENT_DATE())
    ORDER BY USAGE_DATE DESC
    """
    return run_query(query)


def get_cortex_functions_usage(days: int = 7) -> Optional[pd.DataFrame]:
    """
    Get Cortex function usage aggregated by hour.
    Note: Does not include query_id for attribution.
    """
    query = f"""
    SELECT 
        START_TIME,
        END_TIME,
        FUNCTION_NAME,
        MODEL_NAME,
        WAREHOUSE_ID,
        TOKEN_CREDITS,
        TOKENS
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_USAGE_HISTORY
    WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
    ORDER BY START_TIME DESC
    """
    return run_query(query)


def get_cortex_functions_query_usage(days: int = 7) -> Optional[pd.DataFrame]:
    """
    Get Cortex function usage at the query level.
    Includes query_id for joining with QUERY_HISTORY.
    """
    query = f"""
    SELECT 
        QUERY_ID,
        FUNCTION_NAME,
        MODEL_NAME,
        TOKENS,
        TOKEN_CREDITS
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY
    ORDER BY TOKEN_CREDITS DESC
    LIMIT 1000
    """
    return run_query(query)


def get_top_expensive_cortex_queries(days: int = 7, limit: int = 50) -> Optional[pd.DataFrame]:
    """
    Get the most expensive Cortex AI queries with user and query details.
    """
    query = f"""
    SELECT 
        c.QUERY_ID,
        LEFT(q.QUERY_TEXT, 200) as QUERY_TEXT,
        q.START_TIME,
        q.EXECUTION_TIME / 1000 as EXECUTION_SECONDS,
        c.FUNCTION_NAME,
        c.MODEL_NAME,
        c.TOKENS,
        c.TOKEN_CREDITS,
        q.USER_NAME,
        q.WAREHOUSE_NAME,
        q.ROLE_NAME
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY c
    JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q
        ON c.QUERY_ID = q.QUERY_ID
    WHERE q.START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
    ORDER BY c.TOKEN_CREDITS DESC
    LIMIT {limit}
    """
    return run_query(query)


def get_cortex_usage_by_user(days: int = 7) -> Optional[pd.DataFrame]:
    """
    Get Cortex AI usage aggregated by user.
    """
    query = f"""
    SELECT 
        q.USER_NAME,
        c.MODEL_NAME,
        COUNT(*) as QUERY_COUNT,
        SUM(c.TOKENS) as TOTAL_TOKENS,
        SUM(c.TOKEN_CREDITS) as TOTAL_CREDITS
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY c
    JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q
        ON c.QUERY_ID = q.QUERY_ID
    WHERE q.START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
    GROUP BY q.USER_NAME, c.MODEL_NAME
    ORDER BY TOTAL_CREDITS DESC
    """
    return run_query(query)


def get_cortex_usage_by_function(days: int = 7) -> Optional[pd.DataFrame]:
    """
    Get Cortex AI usage aggregated by function.
    Uses QUERY_HISTORY to filter by date since CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY
    may not have START_TIME column.
    """
    query = f"""
    SELECT 
        c.FUNCTION_NAME,
        c.MODEL_NAME,
        COUNT(*) as INVOCATION_COUNT,
        SUM(c.TOKENS) as TOTAL_TOKENS,
        SUM(c.TOKEN_CREDITS) as TOTAL_CREDITS,
        AVG(c.TOKENS) as AVG_TOKENS_PER_CALL
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY c
    JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q
        ON c.QUERY_ID = q.QUERY_ID
    WHERE q.START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
    GROUP BY c.FUNCTION_NAME, c.MODEL_NAME
    ORDER BY TOTAL_CREDITS DESC
    """
    return run_query(query)


def get_cortex_search_usage(days: int = 30) -> Optional[pd.DataFrame]:
    """
    Get Cortex Search daily usage.
    """
    query = f"""
    SELECT *
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_DAILY_USAGE_HISTORY
    WHERE USAGE_DATE >= DATEADD(day, -{days}, CURRENT_DATE())
    ORDER BY USAGE_DATE DESC
    """
    return run_query(query)


def get_cortex_analyst_usage(days: int = 30) -> Optional[pd.DataFrame]:
    """
    Get Cortex Analyst usage history.
    """
    query = f"""
    SELECT *
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_ANALYST_USAGE_HISTORY
    WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
    ORDER BY START_TIME DESC
    """
    return run_query(query)


def count_tokens_sample(table_name: str, column_name: str, model: str = "llama3.1-8b", sample_size: int = 1000) -> Optional[pd.DataFrame]:
    """
    Get token count statistics for a sample of rows.
    Useful for estimating costs before processing.
    
    Note: Requires appropriate permissions on the target table.
    """
    query = f"""
    SELECT 
        COUNT(*) as SAMPLE_SIZE,
        AVG(AI_COUNT_TOKENS('{model}', {column_name})) as AVG_TOKENS,
        MIN(AI_COUNT_TOKENS('{model}', {column_name})) as MIN_TOKENS,
        MAX(AI_COUNT_TOKENS('{model}', {column_name})) as MAX_TOKENS,
        STDDEV(AI_COUNT_TOKENS('{model}', {column_name})) as STDDEV_TOKENS
    FROM (
        SELECT {column_name}
        FROM {table_name}
        SAMPLE ({sample_size} ROWS)
    )
    """
    return run_query(query, ttl=300)  # 5 minute cache


# ============================================
# Helper Functions
# ============================================

def check_account_usage_access() -> bool:
    """
    Check if the current user has access to ACCOUNT_USAGE views.
    """
    query = """
    SELECT COUNT(*) as cnt 
    FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY 
    LIMIT 1
    """
    result = run_query(query)
    return result is not None and len(result) > 0


def get_available_models() -> Optional[pd.DataFrame]:
    """
    Get list of available Cortex models by checking CORTEX_MODELS_ALLOWLIST.
    Falls back to showing all models if parameter not set.
    """
    query = """
    SHOW PARAMETERS LIKE 'CORTEX_MODELS_ALLOWLIST' IN ACCOUNT
    """
    return run_query(query)
