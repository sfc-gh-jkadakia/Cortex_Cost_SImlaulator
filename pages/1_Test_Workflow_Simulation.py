"""
Test Workflow - Multi-Query Testing & Comparison
================================================
Run multiple queries, compare approaches (COMPLETE vs CLASSIFY), analyze at scale
"""

import streamlit as st
import pandas as pd
import altair as alt
import time
import json
from datetime import datetime
import sys

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from utils.branding import apply_snowflake_branding, render_sidebar_branding
from utils.pricing import CORTEX_MODELS, calculate_cost, estimate_tokens_from_text

st.set_page_config(
    page_title="Test Workflow | Cortex AI Cost Simulator",
    page_icon="❄️",
    layout="wide"
)

apply_snowflake_branding()

# =============================================
# ALL MODELS - from pricing.py
# =============================================
ALL_MODELS = list(CORTEX_MODELS.keys())

# Get allowed models from session (set on Home page)
if 'allowed_models' not in st.session_state:
    st.session_state.allowed_models = ALL_MODELS.copy()

ALLOWED_MODELS = [m for m in st.session_state.allowed_models if m in CORTEX_MODELS]

# =============================================
# SESSION STATE FOR TESTS
# =============================================
if 'test_sessions' not in st.session_state:
    st.session_state.test_sessions = []  # List of test runs
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1

# =============================================
# SNOWFLAKE CONNECTION
# =============================================
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
            return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        raise e

conn = get_connection()

# =============================================
# SIDEBAR - Organized: Name → Version → Navigation → Options
# =============================================
with st.sidebar:
    # 1. APP NAME
    st.markdown("## ❄️ Cortex AI Cost Simulator")
    
    # 2. VERSION
    st.caption("v2.0 - Multi-Query Testing")
    
    st.divider()
    
    # 3. PAGE NAVIGATION
    st.markdown("### 📑 Navigation")
    st.markdown("[🏠 Home](../)")
    st.markdown("**🧪 Simulation** ← You are here")
    st.markdown("[⚡ Real-Time](Test_Workflow_Real_Time)")
    st.markdown("[📊 Usage & Alerts](Usage_and_Alerts)")
    
    st.divider()
    
    # 4. MODEL SELECTION - Simplified
    st.markdown("### ⚙️ Model Selection")
    
    # Get unique vendors
    vendors = list(set(p.provider for p in CORTEX_MODELS.values()))
    vendors.sort()
    
    # Get top 5 cheapest models
    top5_cheapest = sorted(CORTEX_MODELS.items(), key=lambda x: x[1].input_credits)[:5]
    top5_names = [m[0] for m in top5_cheapest]
    
    # Filter options
    filter_option = st.selectbox(
        "Filter Models",
        options=["All Models", "Top 5 Cheapest"] + [f"Vendor: {v}" for v in vendors],
        index=0,
        key="model_filter_sim"
    )
    
    # Apply filter
    if filter_option == "All Models":
        filtered_models = ALL_MODELS.copy()
    elif filter_option == "Top 5 Cheapest":
        filtered_models = top5_names
    else:
        # Vendor filter
        vendor_name = filter_option.replace("Vendor: ", "")
        filtered_models = [m for m, p in CORTEX_MODELS.items() if p.provider == vendor_name]
    
    # Auto-select all filtered models when filter changes
    filter_key = f"last_filter_sim"
    if filter_key not in st.session_state:
        st.session_state[filter_key] = filter_option
    
    # If filter changed, auto-select all models in new filter
    if st.session_state[filter_key] != filter_option:
        st.session_state[filter_key] = filter_option
        st.session_state.allowed_models = filtered_models.copy()
    
    # Model multiselect
    selected = st.multiselect(
        "Select Models",
        options=filtered_models,
        default=[m for m in st.session_state.allowed_models if m in filtered_models] or filtered_models,
        key=f"model_select_sim_{filter_option.replace(' ', '_').replace(':', '')}"
    )
    
    # Update session state
    st.session_state.allowed_models = selected
    
    # Show count
    st.caption(f"✓ {len(selected)} model(s) selected")
    
    st.divider()
    
    # 5. TEST SESSIONS
    st.markdown("### 📋 Test Sessions")
    
    if st.session_state.test_sessions:
        for i, session in enumerate(st.session_state.test_sessions):
            with st.expander(f"Test {i+1}: {session['name'][:15]}...", expanded=False):
                st.caption(f"Type: {session['test_type']}")
                st.caption(f"Results: {len(session.get('results', []))}")
                if st.button("Delete", key=f"del_{i}"):
                    st.session_state.test_sessions.pop(i)
                    st.rerun()
    else:
        st.caption("No tests yet")
    
    st.divider()
    
    # Branding at bottom
    render_sidebar_branding()

# Update ALLOWED_MODELS after potential sidebar changes
ALLOWED_MODELS = [m for m in st.session_state.allowed_models if m in CORTEX_MODELS]

# =============================================
# HEADER
# =============================================
st.title("🧪 Test Workflow")

# Progress indicator
steps = ["1. Create Test", "2. Run Models", "3. Scale Costs", "4. Compare All"]
step_cols = st.columns(4)
for i, step in enumerate(steps):
    with step_cols[i]:
        if i + 1 < st.session_state.current_step:
            st.success(f"✅ {step}")
        elif i + 1 == st.session_state.current_step:
            st.info(f"▶️ {step}")
        else:
            st.markdown(f"⬜ {step}")

st.divider()

# =============================================
# STEP 1: CREATE TEST
# =============================================
if st.session_state.current_step == 1:
    st.header("Step 1: Create Test")
    
    # Check allowed models
    if not ALLOWED_MODELS:
        st.error("❌ No models selected! Go to Home page and select models in sidebar.")
        st.stop()
    
    st.success(f"✅ {len(ALLOWED_MODELS)} models available for testing")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Test type selection
        test_type = st.selectbox(
            "Test Type",
            options=[
                "COMPLETE - Custom Prompt",
                "COMPLETE - Summarize",
                "COMPLETE - Classify",
                "COMPLETE - Extract",
                "SENTIMENT - Built-in",
                "SUMMARIZE - Built-in",
                "Compare: COMPLETE vs SENTIMENT",
                "Compare: COMPLETE vs SUMMARIZE",
            ],
            help="Choose the AI function or comparison to test"
        )
        
        # Test name
        test_name = st.text_input(
            "Test Name",
            value=f"Test {len(st.session_state.test_sessions) + 1}: {test_type}",
            help="Give this test a memorable name"
        )
        
        # Prompt templates based on test type
        if "Custom Prompt" in test_type:
            prompt = st.text_area(
                "Custom Prompt",
                height=120,
                placeholder="Enter your prompt. Use {text} as placeholder for sample data.",
                value="Analyze the following and provide insights:\n\n{text}"
            )
        elif "Summarize" in test_type and "COMPLETE" in test_type:
            prompt = st.text_area(
                "Summarize Prompt",
                value="Summarize the following text in 2-3 concise sentences:\n\n{text}",
                height=100
            )
        elif "Classify" in test_type:
            categories = st.text_input("Categories (comma-separated)", value="Positive, Negative, Neutral, Mixed")
            prompt = f"Classify the following text into one of these categories: [{categories}]. Respond with only the category name.\n\nText: {{text}}"
            st.code(prompt, language=None)
        elif "Extract" in test_type:
            prompt = "Extract key entities (names, dates, locations, amounts) from this text as JSON:\n\n{text}"
            st.code(prompt, language=None)
        elif "SENTIMENT" in test_type and "Compare" not in test_type:
            prompt = None  # Built-in function
            st.info("SENTIMENT is a built-in function - no prompt needed")
        elif "SUMMARIZE" in test_type and "Compare" not in test_type:
            prompt = None  # Built-in function
            st.info("SUMMARIZE is a built-in function - no prompt needed")
        elif "Compare" in test_type:
            prompt = st.text_area(
                "COMPLETE Prompt (for comparison)",
                value="Summarize: {text}" if "SUMMARIZE" in test_type else "Analyze sentiment (POSITIVE/NEGATIVE/NEUTRAL): {text}",
                height=80
            )
            st.caption("Will also run built-in function for comparison")
        
        # Sample text
        sample_text = st.text_area(
            "Sample Text",
            height=150,
            placeholder="Paste sample data to test with...",
            value=""
        )
    
    with col2:
        st.markdown("##### Model Selection")
        
        # Model selection from allowed list
        select_mode = st.radio("Select by:", ["Tier", "Manual"], horizontal=True)
        
        if select_mode == "Tier":
            # Group allowed models by tier
            budget = [m for m in ["llama3.2-1b", "llama3.2-3b", "mistral-7b", "gemma-7b"] if m in ALLOWED_MODELS]
            balanced = [m for m in ["llama3.1-8b", "mixtral-8x7b", "snowflake-arctic"] if m in ALLOWED_MODELS]
            premium = [m for m in ["llama3.1-70b", "mistral-large", "mistral-large2", "claude-3-5-sonnet"] if m in ALLOWED_MODELS]
            
            tier = st.selectbox("Tier", options=["Budget", "Balanced", "Premium", "All Allowed"])
            
            if tier == "Budget":
                models_to_test = budget
            elif tier == "Balanced":
                models_to_test = balanced
            elif tier == "Premium":
                models_to_test = premium
            else:
                models_to_test = ALLOWED_MODELS
            
            st.caption(f"Models: {', '.join(models_to_test) if models_to_test else 'None in this tier'}")
        else:
            models_to_test = st.multiselect(
                "Select Models",
                options=ALLOWED_MODELS,
                default=ALLOWED_MODELS[:3] if len(ALLOWED_MODELS) >= 3 else ALLOWED_MODELS
            )
        
        st.markdown("##### Quick Stats")
        if sample_text:
            tokens = estimate_tokens_from_text(sample_text)
            st.metric("Input Tokens", f"{tokens:,}")
            
            # Estimate output
            if "Sentiment" in test_type or "Classify" in test_type:
                est_output = 10
            elif "Summarize" in test_type:
                est_output = 100
            else:
                est_output = 150
            st.metric("Est. Output", f"~{est_output}")
        else:
            st.info("Enter sample text")
    
    # Create test button
    st.divider()
    col1, col2 = st.columns([3, 1])
    with col2:
        can_create = sample_text and models_to_test and (prompt or "Built-in" in test_type or "Compare" in test_type)
        if st.button("Create Test →", type="primary", use_container_width=True, disabled=not can_create):
            # Store test config
            new_test = {
                "name": test_name,
                "test_type": test_type,
                "prompt": prompt if prompt else None,
                "sample_text": sample_text,
                "models": models_to_test,
                "input_tokens": estimate_tokens_from_text(sample_text),
                "results": [],
                "created_at": datetime.now().isoformat()
            }
            st.session_state.test_sessions.append(new_test)
            st.session_state.current_test_idx = len(st.session_state.test_sessions) - 1
            st.session_state.current_step = 2
            st.rerun()

# =============================================
# STEP 2: RUN MODELS
# =============================================
elif st.session_state.current_step == 2:
    st.header("Step 2: Run Models")
    
    if not st.session_state.test_sessions:
        st.error("No test created. Go back to Step 1.")
        if st.button("← Back"):
            st.session_state.current_step = 1
            st.rerun()
        st.stop()
    
    # Get current test
    test_idx = st.session_state.get('current_test_idx', len(st.session_state.test_sessions) - 1)
    test = st.session_state.test_sessions[test_idx]
    
    # Show test config
    st.markdown(f"**Test:** {test['name']}")
    with st.expander("Test Configuration", expanded=False):
        st.write(f"**Type:** {test['test_type']}")
        st.write(f"**Models:** {', '.join(test['models'])}")
        st.write(f"**Input Tokens:** {test['input_tokens']}")
        if test['prompt']:
            st.code(test['prompt'][:200] + "..." if len(test['prompt']) > 200 else test['prompt'])
    
    if conn is None:
        st.error("❌ Snowflake connection required")
        st.stop()
    
    st.success("✅ Connected to Snowflake")
    
    # Run tests
    if not test['results']:
        if st.button("🚀 Run All Tests", type="primary", use_container_width=True):
            results = []
            progress = st.progress(0)
            status = st.empty()
            
            is_comparison = "Compare" in test['test_type']
            
            for i, model in enumerate(test['models']):
                status.text(f"Testing {model}...")
                progress.progress((i + 1) / len(test['models']))
                
                try:
                    # Build query based on test type
                    safe_text = test['sample_text'].replace("'", "''")
                    
                    if "SENTIMENT - Built-in" in test['test_type']:
                        query = f"SELECT SNOWFLAKE.CORTEX.SENTIMENT('{safe_text}') as response"
                    elif "SUMMARIZE - Built-in" in test['test_type']:
                        query = f"SELECT SNOWFLAKE.CORTEX.SUMMARIZE('{safe_text}') as response"
                    else:
                        # COMPLETE function
                        final_prompt = test['prompt'].replace("{text}", test['sample_text'])
                        safe_prompt = final_prompt.replace("'", "''")
                        query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', '{safe_prompt}') as response"
                    
                    start = time.time()
                    result = run_query(conn, query)
                    elapsed = time.time() - start
                    
                    response = str(result.iloc[0]['RESPONSE'])
                    output_tokens = estimate_tokens_from_text(response)
                    cost = calculate_cost(model, test['input_tokens'], output_tokens)
                    
                    results.append({
                        "model": model,
                        "function": "COMPLETE" if test['prompt'] else test['test_type'].split(" - ")[0],
                        "response": response,
                        "output_tokens": output_tokens,
                        "latency": elapsed,
                        "cost": cost['total_cost_usd'],
                        "status": "success"
                    })
                    
                    # If comparison, also run built-in
                    if is_comparison:
                        if "SENTIMENT" in test['test_type']:
                            builtin_query = f"SELECT SNOWFLAKE.CORTEX.SENTIMENT('{safe_text}') as response"
                            builtin_func = "SENTIMENT"
                        else:
                            builtin_query = f"SELECT SNOWFLAKE.CORTEX.SUMMARIZE('{safe_text}') as response"
                            builtin_func = "SUMMARIZE"
                        
                        start2 = time.time()
                        result2 = run_query(conn, builtin_query)
                        elapsed2 = time.time() - start2
                        
                        response2 = str(result2.iloc[0]['RESPONSE'])
                        # Built-in functions have different cost structure
                        results.append({
                            "model": f"{model} (via {builtin_func})",
                            "function": builtin_func,
                            "response": response2,
                            "output_tokens": estimate_tokens_from_text(response2),
                            "latency": elapsed2,
                            "cost": 0.0001,  # Built-in functions are cheaper
                            "status": "success"
                        })
                        
                except Exception as e:
                    results.append({
                        "model": model,
                        "function": test['test_type'],
                        "response": str(e),
                        "output_tokens": 0,
                        "latency": 0,
                        "cost": 0,
                        "status": "error"
                    })
            
            test['results'] = results
            st.session_state.test_sessions[test_idx] = test
            progress.empty()
            status.empty()
            st.rerun()
    
    # Display results
    if test['results']:
        results = test['results']
        successful = [r for r in results if r['status'] == 'success']
        
        st.markdown(f"### Results ({len(successful)}/{len(results)} successful)")
        
        # Summary metrics
        if successful:
            cols = st.columns(4)
            fastest = min(successful, key=lambda x: x['latency'])
            cheapest = min(successful, key=lambda x: x['cost'])
            
            cols[0].metric("Fastest", fastest['model'][:15], f"{fastest['latency']:.2f}s")
            cols[1].metric("Cheapest", cheapest['model'][:15], f"${cheapest['cost']:.6f}")
            cols[2].metric("Models Tested", len(successful))
            cols[3].metric("Avg Latency", f"{sum(r['latency'] for r in successful)/len(successful):.2f}s")
        
        # Results table
        results_df = pd.DataFrame([
            {
                "Model": r['model'],
                "Function": r['function'],
                "Response": r['response'][:100] + "..." if len(r['response']) > 100 else r['response'],
                "Output Tokens": r['output_tokens'],
                "Latency (s)": r['latency'],
                "Cost ($)": r['cost'],
                "Status": "✅" if r['status'] == 'success' else "❌"
            }
            for r in results
        ])
        
        st.dataframe(results_df, use_container_width=True, hide_index=True)
        
        # Full responses
        with st.expander("View Full Responses"):
            for r in successful:
                st.markdown(f"**{r['model']}** ({r['function']})")
                st.write(r['response'])
                st.divider()
    
    # Navigation
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    with col2:
        if st.button("🔄 Re-run", use_container_width=True):
            test['results'] = []
            st.session_state.test_sessions[test_idx] = test
            st.rerun()
    with col3:
        if st.button("+ New Test", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    with col4:
        if st.button("Next: Scale →", type="primary", use_container_width=True, disabled=not test['results']):
            st.session_state.current_step = 3
            st.rerun()

# =============================================
# STEP 3: SCALE COSTS
# =============================================
elif st.session_state.current_step == 3:
    st.header("Step 3: Scale Cost Simulation")
    
    # Get all test results
    all_results = []
    for i, test in enumerate(st.session_state.test_sessions):
        for r in test.get('results', []):
            if r['status'] == 'success':
                all_results.append({
                    **r,
                    "test_name": test['name'],
                    "test_idx": i
                })
    
    if not all_results:
        st.error("No test results. Run some tests first.")
        if st.button("← Back to Tests"):
            st.session_state.current_step = 2
            st.rerun()
        st.stop()
    
    st.success(f"✅ {len(all_results)} test results available")
    
    # Scale parameters
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Batch Sizes")
        batch_sizes = st.multiselect(
            "Select row counts to simulate",
            options=[10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000],
            default=[100, 1000, 10000, 100000]
        )
    
    with col2:
        st.markdown("##### Cost Settings")
        credit_price = st.number_input("Credit price (USD)", value=3.0, min_value=1.0)
        include_warehouse = st.checkbox("Include warehouse cost estimate", value=False)
    
    if batch_sizes:
        # Calculate scale projections
        scale_data = []
        
        for r in all_results:
            model = r['model']
            base_cost = r['cost']
            
            for batch in batch_sizes:
                total_cost = base_cost * batch
                scale_data.append({
                    "Test": r['test_name'][:20],
                    "Model": model,
                    "Function": r['function'],
                    "Rows": batch,
                    "Total Cost": total_cost,
                    "Cost/Row": base_cost
                })
        
        scale_df = pd.DataFrame(scale_data)
        
        # Pivot table
        st.markdown("### Cost Projections")
        
        # Group by model
        model_pivot = scale_df.groupby(['Model', 'Rows'])['Total Cost'].mean().unstack()
        st.dataframe(
            model_pivot.style.format("${:.2f}").background_gradient(cmap="Blues", axis=None),
            use_container_width=True
        )
        
        # Chart
        st.markdown("### Cost Scaling Chart")
        chart = alt.Chart(scale_df).mark_line(point=True).encode(
            x=alt.X("Rows:Q", scale=alt.Scale(type="log"), title="Rows (log scale)"),
            y=alt.Y("Total Cost:Q", title="Total Cost (USD)"),
            color=alt.Color("Model:N"),
            strokeDash=alt.StrokeDash("Function:N"),
            tooltip=["Model", "Function", "Rows", alt.Tooltip("Total Cost:Q", format="$,.2f")]
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)
        
        # Store for analysis
        st.session_state.scale_df = scale_df
    
    # Navigation
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Back to Tests", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    with col2:
        if st.button("Next: Compare All →", type="primary", use_container_width=True):
            st.session_state.current_step = 4
            st.rerun()

# =============================================
# STEP 4: COMPARE ALL
# =============================================
elif st.session_state.current_step == 4:
    st.header("Step 4: Compare All Tests")
    
    if not st.session_state.test_sessions:
        st.error("No tests to compare.")
        st.stop()
    
    # Gather all results
    all_results = []
    for i, test in enumerate(st.session_state.test_sessions):
        for r in test.get('results', []):
            if r['status'] == 'success':
                all_results.append({
                    "Test": test['name'],
                    "Type": test['test_type'],
                    "Model": r['model'],
                    "Function": r['function'],
                    "Latency (s)": r['latency'],
                    "Cost ($)": r['cost'],
                    "Output Tokens": r['output_tokens'],
                    "Response": r['response']
                })
    
    if not all_results:
        st.warning("No successful test results to compare.")
        st.stop()
    
    results_df = pd.DataFrame(all_results)
    
    # Summary
    st.markdown("### 📊 Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tests", len(st.session_state.test_sessions))
    col2.metric("Total Runs", len(all_results))
    col3.metric("Models Tested", results_df['Model'].nunique())
    col4.metric("Functions Used", results_df['Function'].nunique())
    
    st.divider()
    
    # Comparison table
    st.markdown("### 📋 All Results Comparison")
    
    display_df = results_df.drop(columns=['Response'])
    st.dataframe(
        display_df.style.format({
            "Latency (s)": "{:.2f}",
            "Cost ($)": "${:.6f}"
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Cost by Model & Function")
        cost_chart = alt.Chart(results_df).mark_bar().encode(
            x=alt.X("Model:N"),
            y=alt.Y("Cost ($):Q"),
            color=alt.Color("Function:N"),
            tooltip=["Model", "Function", "Test", alt.Tooltip("Cost ($):Q", format="$.6f")]
        ).properties(height=300)
        st.altair_chart(cost_chart, use_container_width=True)
    
    with col2:
        st.markdown("##### Latency by Model")
        latency_chart = alt.Chart(results_df).mark_bar().encode(
            x=alt.X("Model:N"),
            y=alt.Y("Latency (s):Q"),
            color=alt.Color("Test:N"),
            tooltip=["Model", "Test", alt.Tooltip("Latency (s):Q", format=".2f")]
        ).properties(height=300)
        st.altair_chart(latency_chart, use_container_width=True)
    
    # Winners
    st.markdown("### 🏆 Winners")
    
    cheapest = results_df.loc[results_df['Cost ($)'].idxmin()]
    fastest = results_df.loc[results_df['Latency (s)'].idxmin()]
    
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"💰 **Cheapest:** {cheapest['Model']} ({cheapest['Function']}) - ${cheapest['Cost ($)']:.6f}")
    with col2:
        st.success(f"⚡ **Fastest:** {fastest['Model']} ({fastest['Function']}) - {fastest['Latency (s)']:.2f}s")
    
    # Scale projections if available
    if 'scale_df' in st.session_state:
        st.markdown("### 💵 Projected Savings at Scale")
        scale_df = st.session_state.scale_df
        
        # At 100K rows
        at_100k = scale_df[scale_df['Rows'] == 100000] if 100000 in scale_df['Rows'].values else scale_df[scale_df['Rows'] == scale_df['Rows'].max()]
        if not at_100k.empty:
            cheapest_at_scale = at_100k.loc[at_100k['Total Cost'].idxmin()]
            most_expensive = at_100k.loc[at_100k['Total Cost'].idxmax()]
            savings = most_expensive['Total Cost'] - cheapest_at_scale['Total Cost']
            
            st.markdown(f"""
            At **{int(cheapest_at_scale['Rows']):,} rows**:
            - Cheapest: **{cheapest_at_scale['Model']}** at **${cheapest_at_scale['Total Cost']:,.2f}**
            - Most expensive: **{most_expensive['Model']}** at **${most_expensive['Total Cost']:,.2f}**
            - **Potential savings: ${savings:,.2f}**
            """)
    
    # Export
    st.divider()
    st.markdown("### 📥 Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = results_df.to_csv(index=False)
        st.download_button("📄 Results CSV", csv, "test_results.csv", "text/csv", use_container_width=True)
    
    with col2:
        if 'scale_df' in st.session_state:
            scale_csv = st.session_state.scale_df.to_csv(index=False)
            st.download_button("📊 Scale CSV", scale_csv, "scale_projections.csv", "text/csv", use_container_width=True)
    
    with col3:
        # Summary JSON
        summary = {
            "tests": len(st.session_state.test_sessions),
            "results": len(all_results),
            "cheapest": {"model": cheapest['Model'], "cost": cheapest['Cost ($)']},
            "fastest": {"model": fastest['Model'], "latency": fastest['Latency (s)']}
        }
        st.download_button("📋 Summary JSON", json.dumps(summary, indent=2), "summary.json", "application/json", use_container_width=True)
    
    # Navigation
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← Back to Scale", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()
    with col2:
        if st.button("+ Add More Tests", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    with col3:
        if st.button("🗑️ Clear All & Start Over", use_container_width=True):
            st.session_state.test_sessions = []
            st.session_state.current_step = 1
            if 'scale_df' in st.session_state:
                del st.session_state.scale_df
            st.rerun()
