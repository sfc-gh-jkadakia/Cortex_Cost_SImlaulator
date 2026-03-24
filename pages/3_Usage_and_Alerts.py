"""
Usage & Alerts - Enhanced Dashboard with Real ACCOUNT_USAGE Data
================================================================
5 tabs: Overview, Model Analysis, Reconciliation, Optimization, Alerts
With real usage data from Snowflake ACCOUNT_USAGE views
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from utils.branding import apply_snowflake_branding, render_sidebar_branding
from utils.pricing import CORTEX_MODELS, calculate_cost

st.set_page_config(
    page_title="Usage & Alerts | Cortex AI Cost Simulator",
    page_icon="❄️",
    layout="wide"
)

apply_snowflake_branding()

# Snowflake brand colors for Plotly
SNOWFLAKE_COLORS = [
    '#29B5E8',  # Snowflake Blue
    '#11567F',  # Mid Blue
    '#71D3DC',  # Star Blue
    '#FF9F36',  # Valencia Orange
    '#7D44CF',  # Purple Moon
    '#D45B90',  # First Light
    '#8A999E',  # Windy City
]

# =============================================
# SIDEBAR
# =============================================
with st.sidebar:
    st.markdown("## ❄️ Cortex AI Cost Simulator")
    st.caption("v2.0 - Multi-Query Testing")
    st.divider()
    
    st.markdown("### 📑 Navigation")
    st.markdown("[🏠 Home](../)")
    st.markdown("[🧪 Simulation](Test_Workflow_Simulation)")
    st.markdown("[⚡ Real-Time](Test_Workflow_Real_Time)")
    st.markdown("**📊 Usage & Alerts** ← You are here")
    st.divider()
    
    render_sidebar_branding()

st.title("📊 Real Usage Analytics")
st.markdown("Monitor actual Cortex AI spending from Snowflake ACCOUNT_USAGE views.")

# =============================================
# Snowflake Connection
# =============================================
@st.cache_resource
def get_connection():
    try:
        return st.connection("snowflake")
    except:
        return None

def run_query(conn, sql):
    try:
        with conn.raw_connection.cursor() as cur:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            df = pd.DataFrame(rows, columns=columns)
            # Convert Decimal columns to float for calculations
            for col in df.columns:
                if df[col].dtype == object:
                    try:
                        df[col] = df[col].apply(lambda x: float(x) if x is not None and hasattr(x, '__float__') else x)
                    except:
                        pass
            return df
    except Exception as e:
        raise e

conn = get_connection()

# Data latency warning
st.warning("⚠️ **Data Latency:** ACCOUNT_USAGE views have 2-3 hour latency. Recent activity may not appear yet.")

# =============================================
# FIVE TABS
# =============================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview", 
    "🤖 Model Analysis", 
    "🔄 Reconciliation",
    "💡 Optimization", 
    "🔔 Alerts"
])

# =============================================
# TAB 1: OVERVIEW
# =============================================
with tab1:
    if conn is None:
        st.error("❌ Snowflake connection required.")
    else:
        st.subheader("AI Services Usage Overview")
        
        # Date range selector
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            days = st.selectbox("Time Range", options=[7, 14, 30, 90], index=2, format_func=lambda x: f"Last {x} days")
        with col2:
            credit_price = st.number_input("$/Credit", min_value=1.0, value=3.0, step=0.5)
        
        try:
            # Main AI Services usage from METERING_HISTORY
            usage_query = f"""
            SELECT 
                DATE(START_TIME) as usage_date,
                SERVICE_TYPE,
                SUM(CREDITS_USED) as credits
            FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
            WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
                AND SERVICE_TYPE = 'AI_SERVICES'
            GROUP BY 1, 2
            ORDER BY 1
            """
            usage_df = run_query(conn, usage_query)
            
            if len(usage_df) > 0:
                total_credits = usage_df['CREDITS'].sum()
                total_cost = total_credits * credit_price
                avg_daily = total_credits / days
                projected_monthly = avg_daily * 30
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Credits", f"{total_credits:,.2f}", help=f"Last {days} days")
                col2.metric("Total Cost", f"${total_cost:,.2f}", help=f"At ${credit_price}/credit")
                col3.metric("Avg Daily", f"{avg_daily:,.2f}", f"${avg_daily * credit_price:,.2f}/day")
                col4.metric("Projected Monthly", f"{projected_monthly:,.0f}", f"${projected_monthly * credit_price:,.0f}")
                
                st.divider()
                
                # Daily trend chart with Plotly
                st.markdown("##### Daily Usage Trend")
                
                fig = px.bar(
                    usage_df, 
                    x='USAGE_DATE', 
                    y='CREDITS',
                    color_discrete_sequence=[SNOWFLAKE_COLORS[0]],
                    labels={'USAGE_DATE': 'Date', 'CREDITS': 'Credits Used'}
                )
                fig.update_layout(
                    height=300,
                    showlegend=False,
                    xaxis_title="Date",
                    yaxis_title="Credits"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Forecast
                st.markdown("##### 30-Day Forecast")
                
                daily_totals = usage_df.groupby('USAGE_DATE')['CREDITS'].sum().reset_index()
                if len(daily_totals) > 1:
                    # Simple linear trend
                    x = list(range(len(daily_totals)))
                    y = daily_totals['CREDITS'].values
                    slope = (y[-1] - y[0]) / (len(y) - 1) if len(y) > 1 else 0
                    
                    # Build forecast
                    forecast_data = []
                    for _, row in daily_totals.iterrows():
                        forecast_data.append({
                            'Date': row['USAGE_DATE'],
                            'Credits': row['CREDITS'],
                            'Type': 'Actual'
                        })
                    
                    last_date = daily_totals['USAGE_DATE'].max()
                    last_value = float(daily_totals['CREDITS'].iloc[-1])
                    for i in range(30):
                        forecast_date = pd.to_datetime(last_date) + timedelta(days=i+1)
                        forecast_value = max(last_value + (slope * i), 0)
                        forecast_data.append({
                            'Date': forecast_date,
                            'Credits': forecast_value,
                            'Type': 'Forecast'
                        })
                    
                    forecast_df = pd.DataFrame(forecast_data)
                    
                    fig = px.line(
                        forecast_df,
                        x='Date',
                        y='Credits',
                        color='Type',
                        color_discrete_map={'Actual': SNOWFLAKE_COLORS[0], 'Forecast': SNOWFLAKE_COLORS[3]},
                        markers=True
                    )
                    fig.update_layout(height=250)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No AI_SERVICES usage found in the selected time range.")
                
        except Exception as e:
            st.error(f"Error fetching usage data: {e}")

# =============================================
# TAB 2: MODEL ANALYSIS (NEW)
# =============================================
with tab2:
    if conn is None:
        st.error("❌ Snowflake connection required.")
    else:
        st.subheader("🤖 Model & Function Analysis")
        st.caption("Detailed breakdown from CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            model_days = st.selectbox("Analysis Period", options=[7, 14, 30, 90], index=2, 
                                       format_func=lambda x: f"Last {x} days", key="model_days")
        
        try:
            # Model breakdown query
            model_query = f"""
            SELECT 
                COALESCE(NULLIF(MODEL_NAME, ''), 'Specialized Function') as model_name,
                FUNCTION_NAME,
                COUNT(*) as invocations,
                SUM(TOKENS) as total_tokens,
                SUM(TOKEN_CREDITS) as total_credits,
                AVG(TOKENS) as avg_tokens_per_call,
                AVG(TOKEN_CREDITS) as avg_credits_per_call
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY c
            JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q ON c.QUERY_ID = q.QUERY_ID
            WHERE q.START_TIME >= DATEADD(day, -{model_days}, CURRENT_TIMESTAMP())
            GROUP BY 1, 2
            ORDER BY total_credits DESC
            """
            model_df = run_query(conn, model_query)
            
            if len(model_df) > 0:
                # Summary metrics
                total_invocations = model_df['INVOCATIONS'].sum()
                total_tokens = model_df['TOTAL_TOKENS'].sum()
                total_credits = model_df['TOTAL_CREDITS'].sum()
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Invocations", f"{total_invocations:,}")
                col2.metric("Total Tokens", f"{total_tokens:,.0f}")
                col3.metric("Total Credits", f"{total_credits:,.4f}")
                col4.metric("Avg Tokens/Call", f"{total_tokens/total_invocations:,.0f}" if total_invocations > 0 else "0")
                
                st.divider()
                
                # Model breakdown
                st.markdown("##### Credits by Model")
                
                model_summary = model_df.groupby('MODEL_NAME').agg({
                    'INVOCATIONS': 'sum',
                    'TOTAL_TOKENS': 'sum',
                    'TOTAL_CREDITS': 'sum'
                }).reset_index().sort_values('TOTAL_CREDITS', ascending=False)
                
                fig = px.pie(
                    model_summary,
                    values='TOTAL_CREDITS',
                    names='MODEL_NAME',
                    color_discrete_sequence=SNOWFLAKE_COLORS,
                    hole=0.4
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
                
                # Function breakdown
                st.markdown("##### Credits by Function")
                
                func_summary = model_df.groupby('FUNCTION_NAME').agg({
                    'INVOCATIONS': 'sum',
                    'TOTAL_TOKENS': 'sum',
                    'TOTAL_CREDITS': 'sum'
                }).reset_index().sort_values('TOTAL_CREDITS', ascending=False)
                
                fig = px.bar(
                    func_summary,
                    x='FUNCTION_NAME',
                    y='TOTAL_CREDITS',
                    color='FUNCTION_NAME',
                    color_discrete_sequence=SNOWFLAKE_COLORS
                )
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
                
                # Detailed table
                st.markdown("##### Detailed Breakdown")
                st.dataframe(
                    model_df,
                    column_config={
                        "MODEL_NAME": "Model",
                        "FUNCTION_NAME": "Function",
                        "INVOCATIONS": st.column_config.NumberColumn("Calls", format="%d"),
                        "TOTAL_TOKENS": st.column_config.NumberColumn("Tokens", format="%.0f"),
                        "TOTAL_CREDITS": st.column_config.NumberColumn("Credits", format="%.4f"),
                        "AVG_TOKENS_PER_CALL": st.column_config.NumberColumn("Avg Tokens", format="%.0f"),
                        "AVG_CREDITS_PER_CALL": st.column_config.NumberColumn("Avg Credits", format="%.6f"),
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Export button
                csv = model_df.to_csv(index=False)
                st.download_button(
                    "📥 Export to CSV",
                    csv,
                    "cortex_model_analysis.csv",
                    "text/csv"
                )
                
            else:
                st.info("No function-level usage data found.")
                
        except Exception as e:
            st.error(f"Error fetching model data: {e}")
            st.caption("Make sure you have access to CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY view.")

# =============================================
# TAB 3: RECONCILIATION (NEW)
# =============================================
with tab3:
    if conn is None:
        st.error("❌ Snowflake connection required.")
    else:
        st.subheader("🔄 3-Tier Reconciliation")
        st.caption("Compare AI_SERVICES baseline against sum of individual service tables")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            recon_days = st.selectbox("Reconciliation Period", options=[7, 14, 30, 90], index=2,
                                       format_func=lambda x: f"Last {x} days", key="recon_days")
        
        try:
            # Get AI_SERVICES baseline from METERING_HISTORY
            baseline_query = f"""
            SELECT COALESCE(SUM(CREDITS_USED), 0) as baseline_credits
            FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
            WHERE START_TIME >= DATEADD(day, -{recon_days}, CURRENT_TIMESTAMP())
                AND SERVICE_TYPE = 'AI_SERVICES'
            """
            baseline_df = run_query(conn, baseline_query)
            baseline_credits = float(baseline_df.iloc[0]['BASELINE_CREDITS']) if len(baseline_df) > 0 else 0
            
            # Get individual service totals
            services_data = []
            
            # 1. Cortex Functions (exclude AI_EXTRACT to prevent double counting)
            try:
                cf_query = f"""
                SELECT COALESCE(SUM(TOKEN_CREDITS), 0) as credits
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY c
                JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q ON c.QUERY_ID = q.QUERY_ID
                WHERE q.START_TIME >= DATEADD(day, -{recon_days}, CURRENT_TIMESTAMP())
                    AND c.FUNCTION_NAME != 'AI_EXTRACT'
                """
                cf_df = run_query(conn, cf_query)
                services_data.append({
                    'Service': 'Cortex Functions',
                    'Credits': float(cf_df.iloc[0]['CREDITS']) if len(cf_df) > 0 else 0,
                    'Status': '✅'
                })
            except:
                services_data.append({'Service': 'Cortex Functions', 'Credits': 0, 'Status': '❌ No Access'})
            
            # 2. Cortex Analyst
            try:
                ca_query = f"""
                SELECT COALESCE(SUM(CREDITS), 0) as credits
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_ANALYST_USAGE_HISTORY
                WHERE START_TIME >= DATEADD(day, -{recon_days}, CURRENT_TIMESTAMP())
                """
                ca_df = run_query(conn, ca_query)
                services_data.append({
                    'Service': 'Cortex Analyst',
                    'Credits': float(ca_df.iloc[0]['CREDITS']) if len(ca_df) > 0 else 0,
                    'Status': '✅'
                })
            except:
                services_data.append({'Service': 'Cortex Analyst', 'Credits': 0, 'Status': '❌ No Access'})
            
            # 3. Document Processing
            try:
                dp_query = f"""
                SELECT COALESCE(SUM(CREDITS_USED), 0) as credits
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_DOCUMENT_PROCESSING_USAGE_HISTORY
                WHERE START_TIME >= DATEADD(day, -{recon_days}, CURRENT_TIMESTAMP())
                """
                dp_df = run_query(conn, dp_query)
                services_data.append({
                    'Service': 'Document Processing',
                    'Credits': float(dp_df.iloc[0]['CREDITS']) if len(dp_df) > 0 else 0,
                    'Status': '✅'
                })
            except:
                services_data.append({'Service': 'Document Processing', 'Credits': 0, 'Status': '❌ No Access'})
            
            # 4. Cortex Search
            try:
                cs_query = f"""
                SELECT COALESCE(SUM(CREDITS), 0) as credits
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_SERVING_USAGE_HISTORY
                WHERE START_TIME >= DATEADD(day, -{recon_days}, CURRENT_TIMESTAMP())
                """
                cs_df = run_query(conn, cs_query)
                services_data.append({
                    'Service': 'Cortex Search',
                    'Credits': float(cs_df.iloc[0]['CREDITS']) if len(cs_df) > 0 else 0,
                    'Status': '✅'
                })
            except:
                services_data.append({'Service': 'Cortex Search', 'Credits': 0, 'Status': '❌ No Access'})
            
            # 5. Fine Tuning
            try:
                ft_query = f"""
                SELECT COALESCE(SUM(TOKEN_CREDITS), 0) as credits
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FINE_TUNING_USAGE_HISTORY
                WHERE START_TIME >= DATEADD(day, -{recon_days}, CURRENT_TIMESTAMP())
                """
                ft_df = run_query(conn, ft_query)
                services_data.append({
                    'Service': 'Fine Tuning',
                    'Credits': float(ft_df.iloc[0]['CREDITS']) if len(ft_df) > 0 else 0,
                    'Status': '✅'
                })
            except:
                services_data.append({'Service': 'Fine Tuning', 'Credits': 0, 'Status': '❌ No Access'})
            
            services_df = pd.DataFrame(services_data)
            granular_total = services_df['Credits'].sum()
            
            # Calculate variance
            variance = granular_total - baseline_credits
            variance_pct = (variance / baseline_credits * 100) if baseline_credits > 0 else 0
            coverage_pct = (granular_total / baseline_credits * 100) if baseline_credits > 0 else 0
            
            # Determine status
            if abs(variance_pct) <= 1:
                status = "🟢 EXCELLENT"
                status_color = "green"
            elif abs(variance_pct) <= 5:
                status = "🟡 GOOD"
                status_color = "orange"
            elif abs(variance_pct) <= 15:
                status = "🟠 WARNING"
                status_color = "orange"
            else:
                status = "🔴 CRITICAL"
                status_color = "red"
            
            # Display reconciliation summary
            st.markdown("### Reconciliation Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("AI_SERVICES Baseline", f"{baseline_credits:,.4f}")
            col2.metric("Granular Services Total", f"{granular_total:,.4f}")
            col3.metric("Variance", f"{variance:+,.4f}", f"{variance_pct:+.2f}%")
            col4.metric("Coverage", f"{coverage_pct:.1f}%", status)
            
            # Status indicator
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #29B5E8 0%, #11567F 100%); 
                        padding: 1rem; border-radius: 10px; text-align: center; margin: 1rem 0;">
                <h3 style="color: white; margin: 0;">Reconciliation Status: {status}</h3>
                <p style="color: #E0F7FA; margin: 0.5rem 0;">
                    Variance of {variance_pct:.2f}% between baseline and granular services
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # Service breakdown
            st.markdown("### Service Breakdown")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Pie chart
                fig = px.pie(
                    services_df[services_df['Credits'] > 0],
                    values='Credits',
                    names='Service',
                    color_discrete_sequence=SNOWFLAKE_COLORS,
                    hole=0.4
                )
                fig.update_layout(height=350, title="Credits by Service")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Service table
                st.dataframe(
                    services_df,
                    column_config={
                        "Service": "Service",
                        "Credits": st.column_config.NumberColumn("Credits", format="%.4f"),
                        "Status": "Access"
                    },
                    hide_index=True,
                    use_container_width=True
                )
            
            # Explanation
            with st.expander("ℹ️ Understanding Reconciliation"):
                st.markdown("""
                **3-Tier Reconciliation** compares:
                
                1. **AI_SERVICES Baseline** - Total from METERING_HISTORY (billing source)
                2. **Granular Services** - Sum of individual service tables:
                   - CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY (LLM calls)
                   - CORTEX_ANALYST_USAGE_HISTORY (Semantic layer)
                   - CORTEX_DOCUMENT_PROCESSING_USAGE_HISTORY (Doc AI)
                   - CORTEX_SEARCH_SERVING_USAGE_HISTORY (Vector search)
                   - CORTEX_FINE_TUNING_USAGE_HISTORY (Model training)
                
                **Expected Variance:** ≤2% is normal due to timing differences.
                
                **High Variance Causes:**
                - New service types not yet tracked
                - AI_EXTRACT counted in both Functions and Document Processing
                - Data latency between views
                """)
                
        except Exception as e:
            st.error(f"Error performing reconciliation: {e}")

# =============================================
# TAB 4: OPTIMIZATION
# =============================================
with tab4:
    st.subheader("💡 Optimization Opportunities")
    st.caption("AI-powered recommendations to reduce costs")
    
    if conn is None:
        st.error("❌ Snowflake connection required.")
    else:
        try:
            expensive_query = """
            SELECT 
                COALESCE(NULLIF(c.MODEL_NAME, ''), 'Specialized') as MODEL_NAME,
                c.FUNCTION_NAME,
                COUNT(*) as call_count,
                SUM(c.TOKENS) as total_tokens,
                SUM(c.TOKEN_CREDITS) as total_credits
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY c
            JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q ON c.QUERY_ID = q.QUERY_ID
            WHERE q.START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
            GROUP BY 1, 2
            HAVING total_credits > 0.001
            ORDER BY total_credits DESC
            """
            expensive_df = run_query(conn, expensive_query)
            
            if len(expensive_df) > 0:
                st.markdown("### Detected Optimization Opportunities")
                
                # Premium models that could be replaced
                premium_models = ['claude-3-5-sonnet', 'claude-4-sonnet', 'claude-4-opus', 
                                  'mistral-large2', 'snowflake-llama-3.1-405b']
                simple_functions = ['SENTIMENT', 'CLASSIFY_TEXT', 'TRANSLATE']
                
                opportunities = []
                
                for _, row in expensive_df.iterrows():
                    model = row['MODEL_NAME']
                    func = row['FUNCTION_NAME']
                    credits = float(row['TOTAL_CREDITS'])
                    calls = int(row['CALL_COUNT'])
                    
                    # Check for premium model on simple task
                    if any(pm in model for pm in premium_models) and func in simple_functions:
                        cheap_model = 'llama3.1-8b'
                        if model in CORTEX_MODELS and cheap_model in CORTEX_MODELS:
                            current_rate = CORTEX_MODELS[model].input_credits
                            cheap_rate = CORTEX_MODELS[cheap_model].input_credits
                            savings_pct = (1 - cheap_rate / current_rate) * 100
                            savings_credits = credits * (savings_pct / 100)
                            
                            opportunities.append({
                                'type': 'model_switch',
                                'current': model,
                                'recommended': cheap_model,
                                'function': func,
                                'calls': calls,
                                'current_credits': credits,
                                'potential_savings': savings_credits,
                                'savings_pct': savings_pct
                            })
                    
                    # High-volume COMPLETE that could use smaller model
                    if func == 'COMPLETE' and calls > 1000 and 'llama3.1-70b' in model:
                        opportunities.append({
                            'type': 'model_switch',
                            'current': model,
                            'recommended': 'llama3.1-8b',
                            'function': func,
                            'calls': calls,
                            'current_credits': credits,
                            'potential_savings': credits * 0.8,
                            'savings_pct': 80
                        })
                
                if opportunities:
                    total_savings = sum(o['potential_savings'] for o in opportunities)
                    st.success(f"💰 **Total Potential Savings: {total_savings:.4f} credits (~${total_savings * 3:.2f})**")
                    
                    for i, opp in enumerate(opportunities):
                        st.markdown(f"""
                        <div style="border: 2px solid #FF9F36; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; background: #FFF8E1;">
                            <h4 style="margin: 0; color: #E65100;">🔶 Opportunity #{i+1}: Optimize {opp['function']}</h4>
                            <p style="margin: 0.5rem 0; color: #333;">
                                <strong>Current:</strong> {opp['current']} ({opp['calls']:,} calls, {opp['current_credits']:.4f} credits)<br>
                                <strong>Recommended:</strong> {opp['recommended']}
                            </p>
                            <p style="margin: 0; color: #2E7D32; font-size: 1.1rem; font-weight: bold;">
                                Potential Savings: {opp['savings_pct']:.0f}% (~{opp['potential_savings']:.4f} credits)
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ No obvious optimization opportunities detected. Your usage looks efficient!")
                
                # Usage efficiency chart
                st.markdown("### Model Efficiency Comparison")
                
                if len(expensive_df) > 0:
                    expensive_df['EFFICIENCY'] = expensive_df['TOTAL_TOKENS'] / expensive_df['TOTAL_CREDITS'].replace(0, 1)
                    
                    fig = px.bar(
                        expensive_df.head(10),
                        x='MODEL_NAME',
                        y='EFFICIENCY',
                        color='FUNCTION_NAME',
                        color_discrete_sequence=SNOWFLAKE_COLORS,
                        title="Tokens per Credit (Higher = More Efficient)"
                    )
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info("No usage data found to analyze.")
                
        except Exception as e:
            st.error(f"Error analyzing usage: {e}")
        
        # General tips
        st.markdown("### 💡 General Optimization Tips")
        
        tips = [
            ("Use built-in SENTIMENT for simple analysis", "Built-in functions are optimized and often cheaper than COMPLETE."),
            ("Match model to task complexity", "Don't use claude-4-opus for simple classification - llama3.1-8b works great."),
            ("Batch similar requests", "Group related prompts to reduce overhead."),
            ("Use COUNT_TOKENS before large batches", "Estimate costs without actually running AI functions."),
            ("Cache stable results", "Store AI outputs for repeated queries."),
            ("Consider fine-tuning for specialized tasks", "Custom models can be more efficient for specific use cases."),
        ]
        
        for tip, detail in tips:
            with st.expander(f"💡 {tip}"):
                st.write(detail)

# =============================================
# TAB 5: ALERTS
# =============================================
with tab5:
    st.subheader("🔔 Budget Alerts")
    st.caption("Set thresholds and monitor spending")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Daily Alert")
        daily_threshold = st.number_input("Daily credit threshold:", min_value=0.1, value=10.0, step=1.0)
        daily_enabled = st.checkbox("Enable daily alert", value=True)
        
        st.markdown("##### Weekly Alert")
        weekly_threshold = st.number_input("Weekly credit threshold:", min_value=1.0, value=50.0, step=5.0)
        weekly_enabled = st.checkbox("Enable weekly alert", value=True)
    
    with col2:
        st.markdown("##### Monthly Budget")
        monthly_budget = st.number_input("Monthly credit budget:", min_value=10.0, value=200.0, step=10.0)
        monthly_enabled = st.checkbox("Enable monthly tracking", value=True)
        
        credit_price_alert = st.number_input("Credit price ($):", min_value=1.0, value=3.0, step=0.5, key="alert_price")
    
    if st.button("💾 Save Alert Settings", type="primary"):
        st.session_state['alert_config'] = {
            'daily': {'threshold': daily_threshold, 'enabled': daily_enabled},
            'weekly': {'threshold': weekly_threshold, 'enabled': weekly_enabled},
            'monthly': {'budget': monthly_budget, 'enabled': monthly_enabled},
        }
        st.success("✅ Alert settings saved!")
    
    st.divider()
    
    # Current status
    st.markdown("### Current Status")
    
    if conn:
        try:
            status_query = """
            SELECT 
                SUM(CASE WHEN DATE(START_TIME) = CURRENT_DATE() THEN CREDITS_USED ELSE 0 END) as today,
                SUM(CASE WHEN START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP()) THEN CREDITS_USED ELSE 0 END) as this_week,
                SUM(CASE WHEN START_TIME >= DATE_TRUNC('month', CURRENT_TIMESTAMP()) THEN CREDITS_USED ELSE 0 END) as this_month
            FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
            WHERE SERVICE_TYPE = 'AI_SERVICES'
            """
            status_df = run_query(conn, status_query)
            
            if len(status_df) > 0:
                today_credits = float(status_df.iloc[0]['TODAY'] or 0)
                week_credits = float(status_df.iloc[0]['THIS_WEEK'] or 0)
                month_credits = float(status_df.iloc[0]['THIS_MONTH'] or 0)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    pct = (today_credits / daily_threshold) * 100 if daily_enabled and daily_threshold > 0 else 0
                    color = "🟢" if pct < 80 else "🟡" if pct < 100 else "🔴"
                    st.metric("Today", f"{today_credits:.4f}", f"${today_credits * credit_price_alert:.2f}")
                    st.progress(min(pct/100, 1.0))
                    st.caption(f"{color} {pct:.0f}% of {daily_threshold} limit")
                
                with col2:
                    pct = (week_credits / weekly_threshold) * 100 if weekly_enabled and weekly_threshold > 0 else 0
                    color = "🟢" if pct < 80 else "🟡" if pct < 100 else "🔴"
                    st.metric("This Week", f"{week_credits:.4f}", f"${week_credits * credit_price_alert:.2f}")
                    st.progress(min(pct/100, 1.0))
                    st.caption(f"{color} {pct:.0f}% of {weekly_threshold} limit")
                
                with col3:
                    pct = (month_credits / monthly_budget) * 100 if monthly_enabled and monthly_budget > 0 else 0
                    color = "🟢" if pct < 80 else "🟡" if pct < 100 else "🔴"
                    st.metric("This Month", f"{month_credits:.4f}", f"${month_credits * credit_price_alert:.2f}")
                    st.progress(min(pct/100, 1.0))
                    st.caption(f"{color} {pct:.0f}% of {monthly_budget} budget")
                
                # Active alerts
                st.markdown("### Active Alerts")
                alerts = []
                if today_credits > daily_threshold and daily_enabled:
                    alerts.append(f"🔴 **Daily threshold exceeded:** {today_credits:.4f} > {daily_threshold}")
                if week_credits > weekly_threshold and weekly_enabled:
                    alerts.append(f"🔴 **Weekly threshold exceeded:** {week_credits:.4f} > {weekly_threshold}")
                if month_credits > monthly_budget and monthly_enabled:
                    alerts.append(f"🔴 **Monthly budget exceeded:** {month_credits:.4f} > {monthly_budget}")
                
                if alerts:
                    for alert in alerts:
                        st.error(alert)
                else:
                    st.success("✅ All spending within defined thresholds!")
                    
        except Exception as e:
            st.error(f"Error checking status: {e}")
    else:
        st.info("Connect to Snowflake to see current status.")

# =============================================
# FOOTER
# =============================================
st.divider()
st.caption("Data sourced from Snowflake ACCOUNT_USAGE views | 2-3 hour latency")
