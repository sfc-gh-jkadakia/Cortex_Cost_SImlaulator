"""
Test Workflow - Real Time
=========================
Run actual Cortex AI queries against real Snowflake data
Select Database → Schema → Table → Column and test AI functions
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime
import sys

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from utils.branding import apply_snowflake_branding, render_sidebar_branding
from utils.pricing import CORTEX_MODELS, calculate_cost, get_available_models

st.set_page_config(
    page_title="Test Workflow - Real Time | Cortex AI",
    page_icon="❄️",
    layout="wide"
)

apply_snowflake_branding()

# Snowflake colors
SNOWFLAKE_COLORS = ['#29B5E8', '#11567F', '#71D3DC', '#FF9F36', '#7D44CF', '#D45B90']

# =============================================
# AVAILABLE MODELS from pricing.py (only models that work)
# =============================================
AVAILABLE_MODELS = get_available_models()
ALL_MODELS = list(CORTEX_MODELS.keys())

if 'allowed_models' not in st.session_state:
    st.session_state.allowed_models = AVAILABLE_MODELS.copy()

if 'realtime_results' not in st.session_state:
    st.session_state.realtime_results = []

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
    st.markdown("**⚡ Real-Time** ← You are here")
    st.markdown("[📊 Usage & Alerts](Usage_and_Alerts)")
    st.divider()
    
    st.markdown("### ⚙️ Settings")
    credit_price = st.number_input("Credit Price ($)", min_value=1.0, value=3.0, step=0.5)
    
    st.divider()
    render_sidebar_branding()

# =============================================
# SNOWFLAKE CONNECTION
# =============================================
@st.cache_resource
def get_connection():
    try:
        conn = st.connection("snowflake")
        # Test the connection
        conn.raw_connection.cursor().execute("SELECT 1")
        return conn
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def run_query(conn, sql):
    try:
        with conn.raw_connection.cursor() as cur:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            df = pd.DataFrame(rows, columns=columns)
            # Convert Decimal to float
            for col in df.columns:
                if df[col].dtype == object:
                    try:
                        df[col] = df[col].apply(lambda x: float(x) if x is not None and hasattr(x, '__float__') else x)
                    except:
                        pass
            return df
    except Exception as e:
        raise e

# Clear cache and reconnect button
conn = get_connection()

# =============================================
# HEADER
# =============================================
st.title("⚡ Test Workflow - Real Time")
st.markdown("Run actual Cortex AI functions against your Snowflake data.")

if conn is None:
    st.error("❌ Snowflake connection required. Please configure your connection.")
    if st.button("🔄 Retry Connection"):
        st.cache_resource.clear()
        st.rerun()
    st.stop()

st.warning("⚠️ **This page executes real queries and consumes Snowflake credits.** Use Simulation mode for cost-free testing.")

# =============================================
# STEP 1: SELECT DATA SOURCE
# =============================================
st.markdown("---")
st.markdown("### Step 1: Select Data Source")

col1, col2, col3 = st.columns(3)

# Get databases
@st.cache_data(ttl=300)
def get_databases():
    try:
        df = run_query(conn, "SHOW DATABASES")
        return df['name'].tolist() if 'name' in df.columns else []
    except:
        return []

databases = get_databases()

with col1:
    selected_db = st.selectbox("📁 Database", options=[""] + databases, index=0)

# Get schemas for selected database
@st.cache_data(ttl=300)
def get_schemas(database):
    if not database:
        return []
    try:
        df = run_query(conn, f"SHOW SCHEMAS IN DATABASE {database}")
        return df['name'].tolist() if 'name' in df.columns else []
    except:
        return []

schemas = get_schemas(selected_db) if selected_db else []

with col2:
    selected_schema = st.selectbox("📂 Schema", options=[""] + schemas, index=0, disabled=not selected_db)

# Get tables for selected schema
@st.cache_data(ttl=300)
def get_tables(database, schema):
    if not database or not schema:
        return []
    try:
        df = run_query(conn, f"SHOW TABLES IN {database}.{schema}")
        return df['name'].tolist() if 'name' in df.columns else []
    except:
        return []

tables = get_tables(selected_db, selected_schema) if selected_db and selected_schema else []

with col3:
    selected_table = st.selectbox("📋 Table", options=[""] + tables, index=0, disabled=not selected_schema)

# Get columns for selected table
@st.cache_data(ttl=300)
def get_columns(database, schema, table):
    if not database or not schema or not table:
        return []
    try:
        df = run_query(conn, f"DESCRIBE TABLE {database}.{schema}.{table}")
        # Filter for text-like columns
        text_types = ['VARCHAR', 'STRING', 'TEXT', 'CHAR', 'VARIANT']
        text_cols = df[df['type'].str.upper().str.contains('|'.join(text_types), na=False)]['name'].tolist()
        return text_cols if text_cols else df['name'].tolist()
    except:
        return []

columns = get_columns(selected_db, selected_schema, selected_table) if selected_table else []

col1, col2 = st.columns(2)
with col1:
    selected_column = st.selectbox("📝 Text Column", options=[""] + columns, index=0, disabled=not selected_table)

with col2:
    sample_size = st.selectbox("🔢 Sample Size", options=[5, 10, 25, 50, 100], index=1, 
                                help="Number of rows to test (limits credit usage)")

# Preview data
if selected_db and selected_schema and selected_table and selected_column:
    with st.expander("👁️ Preview Data", expanded=False):
        try:
            preview_query = f"""
            SELECT {selected_column} 
            FROM {selected_db}.{selected_schema}.{selected_table} 
            WHERE {selected_column} IS NOT NULL 
            LIMIT 5
            """
            preview_df = run_query(conn, preview_query)
            st.dataframe(preview_df, use_container_width=True)
            
            # Get total row count
            count_query = f"""
            SELECT COUNT(*) as cnt 
            FROM {selected_db}.{selected_schema}.{selected_table}
            WHERE {selected_column} IS NOT NULL
            """
            count_df = run_query(conn, count_query)
            total_rows = int(count_df.iloc[0]['CNT']) if len(count_df) > 0 else 0
            st.info(f"📊 Total rows with data: **{total_rows:,}**")
        except Exception as e:
            st.error(f"Error previewing data: {e}")

# =============================================
# STEP 2: CONFIGURE TEST
# =============================================
st.markdown("---")
st.markdown("### Step 2: Configure Test")

col1, col2 = st.columns(2)

with col1:
    test_type = st.selectbox(
        "🧪 Test Type",
        options=[
            "COMPLETE - Custom Prompt",
            "SENTIMENT - Analyze Sentiment",
            "SUMMARIZE - Summarize Text",
            "TRANSLATE - Translate Text",
            "CLASSIFY_TEXT - Classify Text",
        ],
        index=0
    )

with col2:
    # Model selection based on test type
    if "COMPLETE" in test_type:
        # Only show models that are available
        available_models = [m for m in AVAILABLE_MODELS if m in CORTEX_MODELS]
        selected_models = st.multiselect(
            "🤖 Models to Compare",
            options=available_models,
            default=available_models[:3] if len(available_models) >= 3 else available_models,
            help="Select models to run the test on (only showing available models)"
        )
    else:
        selected_models = ["Built-in Function"]
        st.info(f"ℹ️ {test_type.split(' - ')[0]} uses Snowflake's built-in function")

# Additional options based on test type
if "COMPLETE" in test_type:
    st.markdown("##### Prompt Template")
    st.caption("Use `{text}` as placeholder for column value. For complex prompts, write your full instruction.")
    
    # Prompt template examples
    with st.expander("📚 Example Prompts", expanded=False):
        st.markdown("""
**Simple Summary:**
```
Summarize the following text in 2-3 sentences:

{text}
```

**JSON Extraction:**
```
Extract key information from this text and return ONLY valid JSON:
{
  "sentiment": "positive/negative/neutral",
  "topics": ["topic1", "topic2"],
  "summary": "brief summary"
}

TEXT:
{text}

JSON:
```

**Claims Analysis (like your example):**
```
Extract data from the claim text. Return ONLY valid JSON:
{
  "moi_referenced": "Yes or No",
  "moi_scale": "Reasonable/Questionable/Excessive/Not Related or NULL",
  "treatment_type_referenced": "Yes or No",
  "treatment_type_scale": "Reasonable/Questionable/Excessive/Not Related or NULL"
}

CLAIM TEXT:
{text}

JSON:
```
        """)
    
    prompt_template = st.text_area(
        "📝 Your Prompt",
        value="""Analyze the following text and extract key information.

Return ONLY valid JSON (no markdown, no explanations):
{
  "summary": "brief 1-2 sentence summary",
  "sentiment": "positive/negative/neutral",
  "key_topics": ["topic1", "topic2"]
}

TEXT:
{text}

JSON:""",
        help="Use {text} as placeholder for the column value. The entire prompt will be sent to the model.",
        height=250
    )
    
    # Show preview of actual prompt
    if selected_column:
        with st.expander("👁️ Preview SQL Query", expanded=False):
            preview_escaped = prompt_template.replace("'", "''")
            preview_escaped = preview_escaped.replace("{text}", f"'' || {selected_column} || ''")
            st.code(f"""SELECT 
    {selected_column} as input_text,
    SNOWFLAKE.CORTEX.COMPLETE(
        '<model_name>',
        '{preview_escaped}'
    ) as output
FROM {selected_db or 'DATABASE'}.{selected_schema or 'SCHEMA'}.{selected_table or 'TABLE'}
WHERE {selected_column} IS NOT NULL
LIMIT {sample_size}""", language="sql")

elif "TRANSLATE" in test_type:
    col1, col2 = st.columns(2)
    with col1:
        source_lang = st.selectbox("From Language", ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh"])
    with col2:
        target_lang = st.selectbox("To Language", ["es", "en", "fr", "de", "it", "pt", "ja", "ko", "zh"])
elif "CLASSIFY_TEXT" in test_type:
    categories = st.text_input(
        "📋 Categories (comma-separated)",
        value="positive, negative, neutral",
        help="Enter the categories to classify into"
    )

# =============================================
# STEP 3: RUN TEST
# =============================================
st.markdown("---")
st.markdown("### Step 3: Run Test")

can_run = selected_db and selected_schema and selected_table and selected_column

if not can_run:
    st.info("👆 Complete Step 1 to enable testing")

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    run_button = st.button("🚀 Run Test", type="primary", disabled=not can_run, use_container_width=True)

with col2:
    if st.button("🗑️ Clear Results", use_container_width=True):
        st.session_state.realtime_results = []
        st.rerun()

if run_button and can_run:
    st.markdown("---")
    st.markdown("### 📊 Results")
    
    results = []
    
    # Build and execute queries based on test type
    func_name = test_type.split(" - ")[0]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    if "COMPLETE" in test_type:
        # Run for each selected model
        for i, model in enumerate(selected_models):
            status_text.text(f"Running {model}...")
            progress_bar.progress((i + 1) / len(selected_models))
            
            try:
                # Build the COMPLETE query
                # First escape single quotes in the prompt template
                escaped_prompt = prompt_template.replace("'", "''")
                # Then replace {text} with column concatenation
                escaped_prompt = escaped_prompt.replace("{text}", f"'' || {selected_column} || ''")
                
                query = f"""
                SELECT 
                    {selected_column} as input_text,
                    SNOWFLAKE.CORTEX.COMPLETE(
                        '{model}',
                        '{escaped_prompt}'
                    ) as output,
                    LENGTH({selected_column}) as input_length
                FROM {selected_db}.{selected_schema}.{selected_table}
                WHERE {selected_column} IS NOT NULL
                LIMIT {sample_size}
                """
                
                start_time = time.time()
                result_df = run_query(conn, query)
                elapsed_time = time.time() - start_time
                
                if len(result_df) > 0:
                    # Estimate tokens (~4 chars per token is a common approximation)
                    result_df['INPUT_TOKENS'] = result_df['INPUT_LENGTH'].apply(lambda x: max(1, int(x / 4)) if x else 0)
                    total_input_tokens = result_df['INPUT_TOKENS'].sum()
                    # Estimate output tokens (roughly based on output length)
                    result_df['OUTPUT_TOKENS'] = result_df['OUTPUT'].apply(lambda x: len(str(x)) // 4 if x else 0)
                    total_output_tokens = result_df['OUTPUT_TOKENS'].sum()
                    
                    # Calculate cost
                    cost_info = calculate_cost(model, int(total_input_tokens), int(total_output_tokens), credit_price)
                    
                    results.append({
                        'model': model,
                        'rows': len(result_df),
                        'input_tokens': total_input_tokens,
                        'output_tokens': total_output_tokens,
                        'total_credits': cost_info['total_credits'],
                        'total_cost': cost_info['total_cost_usd'],
                        'time_seconds': elapsed_time,
                        'sample_output': result_df['OUTPUT'].iloc[0][:500] if len(result_df) > 0 else "",
                        'result_df': result_df
                    })
                    
            except Exception as e:
                st.error(f"Error running {model}: {e}")
                
    else:
        # Built-in functions (SENTIMENT, SUMMARIZE, TRANSLATE, CLASSIFY_TEXT)
        status_text.text(f"Running {func_name}...")
        
        try:
            if func_name == "SENTIMENT":
                query = f"""
                SELECT 
                    {selected_column} as input_text,
                    SNOWFLAKE.CORTEX.SENTIMENT({selected_column}) as output
                FROM {selected_db}.{selected_schema}.{selected_table}
                WHERE {selected_column} IS NOT NULL
                LIMIT {sample_size}
                """
            elif func_name == "SUMMARIZE":
                query = f"""
                SELECT 
                    {selected_column} as input_text,
                    SNOWFLAKE.CORTEX.SUMMARIZE({selected_column}) as output
                FROM {selected_db}.{selected_schema}.{selected_table}
                WHERE {selected_column} IS NOT NULL
                LIMIT {sample_size}
                """
            elif func_name == "TRANSLATE":
                query = f"""
                SELECT 
                    {selected_column} as input_text,
                    SNOWFLAKE.CORTEX.TRANSLATE({selected_column}, '{source_lang}', '{target_lang}') as output
                FROM {selected_db}.{selected_schema}.{selected_table}
                WHERE {selected_column} IS NOT NULL
                LIMIT {sample_size}
                """
            elif func_name == "CLASSIFY_TEXT":
                cat_array = "[" + ",".join([f"'{c.strip()}'" for c in categories.split(",")]) + "]"
                query = f"""
                SELECT 
                    {selected_column} as input_text,
                    SNOWFLAKE.CORTEX.CLASSIFY_TEXT({selected_column}, {cat_array}) as output
                FROM {selected_db}.{selected_schema}.{selected_table}
                WHERE {selected_column} IS NOT NULL
                LIMIT {sample_size}
                """
            
            start_time = time.time()
            result_df = run_query(conn, query)
            elapsed_time = time.time() - start_time
            
            progress_bar.progress(1.0)
            
            if len(result_df) > 0:
                # Estimate tokens for built-in functions
                result_df['INPUT_TOKENS'] = result_df['INPUT_TEXT'].apply(lambda x: len(str(x)) // 4 if x else 0)
                total_input_tokens = result_df['INPUT_TOKENS'].sum()
                
                results.append({
                    'model': func_name,
                    'rows': len(result_df),
                    'input_tokens': total_input_tokens,
                    'output_tokens': 0,
                    'total_credits': total_input_tokens * 0.000001,  # Rough estimate
                    'total_cost': total_input_tokens * 0.000001 * credit_price,
                    'time_seconds': elapsed_time,
                    'sample_output': str(result_df['OUTPUT'].iloc[0])[:500] if len(result_df) > 0 else "",
                    'result_df': result_df
                })
                
        except Exception as e:
            st.error(f"Error running {func_name}: {e}")
    
    progress_bar.empty()
    status_text.empty()
    
    # Store results in session state
    if results:
        st.session_state.realtime_results = results
    
# Display results
if st.session_state.realtime_results:
    results = st.session_state.realtime_results
    
    st.markdown("### 📊 Test Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Models Tested", len(results))
    col2.metric("Total Rows", sum(r['rows'] for r in results))
    col3.metric("Total Tokens", f"{sum(r['input_tokens'] + r['output_tokens'] for r in results):,.0f}")
    col4.metric("Total Cost", f"${sum(r['total_cost'] for r in results):,.4f}")
    
    st.divider()
    
    # Comparison table
    st.markdown("##### Model Comparison")
    
    comparison_data = []
    for r in results:
        comparison_data.append({
            'Model': r['model'],
            'Rows': r['rows'],
            'Input Tokens': r['input_tokens'],
            'Output Tokens': r['output_tokens'],
            'Credits': r['total_credits'],
            'Cost ($)': r['total_cost'],
            'Time (s)': r['time_seconds'],
            'Tokens/Sec': (r['input_tokens'] + r['output_tokens']) / r['time_seconds'] if r['time_seconds'] > 0 else 0
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Highlight cheapest and fastest
    if len(comparison_df) > 1:
        cheapest = comparison_df['Cost ($)'].idxmin()
        fastest = comparison_df['Time (s)'].idxmin()
        
        st.dataframe(
            comparison_df,
            column_config={
                "Model": st.column_config.TextColumn("Model"),
                "Rows": st.column_config.NumberColumn("Rows", format="%d"),
                "Input Tokens": st.column_config.NumberColumn("Input Tokens", format="%.0f"),
                "Output Tokens": st.column_config.NumberColumn("Output Tokens", format="%.0f"),
                "Credits": st.column_config.NumberColumn("Credits", format="%.6f"),
                "Cost ($)": st.column_config.NumberColumn("Cost ($)", format="$%.4f"),
                "Time (s)": st.column_config.NumberColumn("Time (s)", format="%.2f"),
                "Tokens/Sec": st.column_config.NumberColumn("Tokens/Sec", format="%.0f"),
            },
            hide_index=True,
            use_container_width=True
        )
        
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"💚 **Cheapest:** {comparison_df.iloc[cheapest]['Model']} (${comparison_df.iloc[cheapest]['Cost ($)']:.4f})")
        with col2:
            st.info(f"⚡ **Fastest:** {comparison_df.iloc[fastest]['Model']} ({comparison_df.iloc[fastest]['Time (s)']:.2f}s)")
    else:
        st.dataframe(comparison_df, hide_index=True, use_container_width=True)
    
    # Cost comparison chart
    if len(results) > 1:
        st.markdown("##### Cost Comparison")
        
        fig = px.bar(
            comparison_df,
            x='Model',
            y='Cost ($)',
            color='Model',
            color_discrete_sequence=SNOWFLAKE_COLORS
        )
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Sample outputs
    st.markdown("##### Sample Outputs")
    
    for r in results:
        with st.expander(f"🤖 {r['model']} Output Sample"):
            st.text(r['sample_output'])
            
            # Show full results table
            if 'result_df' in r and len(r['result_df']) > 0:
                st.markdown("**Full Results:**")
                display_df = r['result_df'][['INPUT_TEXT', 'OUTPUT']].head(10)
                display_df.columns = ['Input', 'Output']
                st.dataframe(display_df, use_container_width=True)
    
    # =============================================
    # STEP 4: SCALE PROJECTION (1K to 100K rows)
    # =============================================
    st.markdown("---")
    st.markdown("### 📈 Scale Projections")
    st.markdown("Estimated costs based on your sample test results")
    
    # Calculate per-row metrics from results
    if results:
        # Fixed scale points
        scale_points = [1000, 5000, 10000, 25000, 50000, 100000]
        
        # Build projection data
        projection_data = []
        for r in results:
            if r['rows'] > 0:
                tokens_per_row = (r['input_tokens'] + r['output_tokens']) / r['rows']
                cost_per_row = r['total_cost'] / r['rows']
                time_per_row = r['time_seconds'] / r['rows']
                
                for scale in scale_points:
                    projection_data.append({
                        'Model': r['model'],
                        'Rows': scale,
                        'Est. Tokens': int(tokens_per_row * scale),
                        'Est. Cost ($)': cost_per_row * scale,
                        'Est. Time (min)': (time_per_row * scale) / 60
                    })
        
        if projection_data:
            projection_df = pd.DataFrame(projection_data)
            
            # Create pivot table for better display
            st.markdown("##### Cost by Scale (1K - 100K rows)")
            
            # Cost pivot
            cost_pivot = projection_df.pivot(index='Rows', columns='Model', values='Est. Cost ($)').reset_index()
            cost_pivot['Rows'] = cost_pivot['Rows'].apply(lambda x: f"{x:,}")
            
            # Format cost columns
            for col in cost_pivot.columns:
                if col != 'Rows':
                    cost_pivot[col] = cost_pivot[col].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(cost_pivot, hide_index=True, use_container_width=True)
            
            # Line chart of projections
            fig = px.line(
                projection_df,
                x='Rows',
                y='Est. Cost ($)',
                color='Model',
                markers=True,
                color_discrete_sequence=SNOWFLAKE_COLORS,
                title="Cost Projection: 1K to 100K Rows"
            )
            fig.update_layout(
                height=400,
                xaxis_title="Number of Rows",
                yaxis_title="Estimated Cost ($)",
                xaxis=dict(tickformat=",")
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary at key scales
            st.markdown("##### Quick Reference")
            
            col1, col2, col3 = st.columns(3)
            
            # Find cheapest at each scale
            for i, (scale, col) in enumerate(zip([1000, 10000, 100000], [col1, col2, col3])):
                scale_data = projection_df[projection_df['Rows'] == scale]
                if len(scale_data) > 0:
                    cheapest_idx = scale_data['Est. Cost ($)'].idxmin()
                    cheapest_model = scale_data.loc[cheapest_idx, 'Model']
                    cheapest_cost = scale_data.loc[cheapest_idx, 'Est. Cost ($)']
                    
                    most_expensive_idx = scale_data['Est. Cost ($)'].idxmax()
                    most_expensive_cost = scale_data.loc[most_expensive_idx, 'Est. Cost ($)']
                    
                    with col:
                        st.markdown(f"**{scale:,} Rows**")
                        st.success(f"💚 Best: {cheapest_model}\n${cheapest_cost:,.2f}")
                        if len(scale_data) > 1:
                            savings = most_expensive_cost - cheapest_cost
                            st.caption(f"Saves ${savings:,.2f} vs most expensive")
            
            # Get actual table row count if available
            if selected_db and selected_schema and selected_table and selected_column:
                try:
                    count_query = f"""
                    SELECT COUNT(*) as cnt 
                    FROM {selected_db}.{selected_schema}.{selected_table}
                    WHERE {selected_column} IS NOT NULL
                    """
                    count_df = run_query(conn, count_query)
                    total_rows = int(count_df.iloc[0]['CNT']) if len(count_df) > 0 else 0
                    
                    if total_rows > 0:
                        st.markdown("---")
                        st.markdown(f"##### 🎯 Your Table: {total_rows:,} rows")
                        
                        # Calculate for actual table size
                        full_projection = []
                        for r in results:
                            if r['rows'] > 0:
                                cost_per_row = r['total_cost'] / r['rows']
                                time_per_row = r['time_seconds'] / r['rows']
                                full_cost = cost_per_row * total_rows
                                full_time = (time_per_row * total_rows) / 60  # in minutes
                                full_projection.append({
                                    'Model': r['model'],
                                    'Est. Cost ($)': full_cost,
                                    'Est. Time (min)': full_time
                                })
                        
                        full_df = pd.DataFrame(full_projection).sort_values('Est. Cost ($)')
                        
                        if len(full_df) > 0:
                            # Display table
                            display_full = full_df.copy()
                            display_full['Est. Cost ($)'] = display_full['Est. Cost ($)'].apply(lambda x: f"${x:,.2f}")
                            display_full['Est. Time (min)'] = display_full['Est. Time (min)'].apply(lambda x: f"{x:,.1f}")
                            st.dataframe(display_full, hide_index=True, use_container_width=True)
                            
                            # Highlight best/worst
                            cheapest = full_df.iloc[0]
                            most_expensive = full_df.iloc[-1]
                            savings = most_expensive['Est. Cost ($)'] - cheapest['Est. Cost ($)']
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.success(f"💚 **Recommended:** {cheapest['Model']}\n\n**${cheapest['Est. Cost ($)']:,.2f}** for {total_rows:,} rows")
                            with col2:
                                if len(full_df) > 1:
                                    st.error(f"💸 **Most Expensive:** {most_expensive['Model']}\n\n**${most_expensive['Est. Cost ($)']:,.2f}** for {total_rows:,} rows")
                            
                            if savings > 0:
                                st.info(f"💰 **Potential Savings:** ${savings:,.2f} ({(savings/most_expensive['Est. Cost ($)']*100):,.1f}%) by choosing {cheapest['Model']}")
                            
                except Exception as e:
                    st.error(f"Error calculating table projections: {e}")
    
    # Export
    st.markdown("---")
    if comparison_data:
        csv = pd.DataFrame(comparison_data).to_csv(index=False)
        st.download_button(
            "📥 Export Results to CSV",
            csv,
            "cortex_realtime_results.csv",
            "text/csv"
        )

# =============================================
# FOOTER
# =============================================
st.markdown("---")
st.caption("⚡ Real-Time Testing | Queries consume Snowflake credits")
