"""
Cortex AI Cost Simulator v2
===========================
Home page with model info, costs, and navigation
"""

import streamlit as st
import pandas as pd
import altair as alt
import sys

sys.path.insert(0, str(__file__).rsplit("/", 1)[0])

from utils.branding import apply_snowflake_branding, render_sidebar_branding
from utils.pricing import CORTEX_MODELS, calculate_cost, get_models_dataframe

st.set_page_config(
    page_title="Cortex AI Cost Simulator",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_snowflake_branding()

# =============================================
# ALL AVAILABLE MODELS - from pricing.py
# =============================================
ALL_MODELS = list(CORTEX_MODELS.keys())

# Initialize session state for allowed models
if 'allowed_models' not in st.session_state:
    st.session_state.allowed_models = ALL_MODELS.copy()

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
    st.markdown("**🏠 Home** ← You are here")
    st.markdown("[🧪 Simulation](Test_Workflow_Simulation)")
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
        key="model_filter_home"
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
    filter_key = f"last_filter_home"
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
        key=f"model_select_home_{filter_option.replace(' ', '_').replace(':', '')}"
    )
    
    # Update session state
    st.session_state.allowed_models = selected
    
    # Show count
    st.caption(f"✓ {len(selected)} model(s) selected")
    
    st.divider()
    
    # Branding at bottom
    render_sidebar_branding()

# =============================================
# HEADER
# =============================================
st.title("❄️ Cortex AI Cost Simulator")
st.markdown("Compare models, test queries, and optimize your Cortex AI costs.")

# =============================================
# QUICK START - Navigation Cards
# =============================================
st.markdown("### 🚀 Quick Start")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #29B5E8 0%, #1B3A4B 100%); padding: 1.5rem; border-radius: 10px; text-align: center; min-height: 180px;">
        <h3 style="color: white; margin: 0;">🧪 Test & Compare</h3>
        <p style="color: #E0F7FA; margin: 0.5rem 0;">Run queries on multiple models, compare results and costs</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Start Testing →", key="btn_workflow", use_container_width=True, type="primary"):
        st.info("👈 Go to **Test Workflow** in sidebar")

with col2:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #29B5E8 0%, #1B3A4B 100%); padding: 1.5rem; border-radius: 10px; text-align: center; min-height: 180px;">
        <h3 style="color: white; margin: 0;">📊 Usage Monitor</h3>
        <p style="color: #E0F7FA; margin: 0.5rem 0;">View actual usage from ACCOUNT_USAGE, set alerts</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("View Usage →", key="btn_usage", use_container_width=True):
        st.info("👈 Go to **Usage & Alerts** in sidebar")

with col3:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #29B5E8 0%, #1B3A4B 100%); padding: 1.5rem; border-radius: 10px; text-align: center; min-height: 180px;">
        <h3 style="color: white; margin: 0;">📋 Model Catalog</h3>
        <p style="color: #E0F7FA; margin: 0.5rem 0;">Browse all models, pricing, and capabilities</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("View Models ↓", key="btn_models", use_container_width=True):
        st.info("👇 Scroll down to see model catalog")

st.divider()

# =============================================
# KEY METRICS
# =============================================
st.markdown("### 💡 Key Insights")

col1, col2, col3, col4 = st.columns(4)

# Calculate price range from allowed models
allowed_models_data = [CORTEX_MODELS[m] for m in st.session_state.allowed_models if m in CORTEX_MODELS]
if allowed_models_data:
    min_price = min(m.input_credits for m in allowed_models_data)
    max_price = max(m.input_credits for m in allowed_models_data)
    price_ratio = max_price / min_price if min_price > 0 else 0
else:
    price_ratio = 0

with col1:
    st.metric("Price Range", f"{price_ratio:.0f}x", help="Ratio between cheapest and most expensive selected model")
with col2:
    st.metric("Models Selected", f"{len(st.session_state.allowed_models)}", help="Models available for testing")
with col3:
    st.metric("Potential Savings", "Up to 95%", help="By choosing the right model for your task")
with col4:
    st.metric("Output vs Input", "3-5x", help="Output tokens typically cost 3-5x more than input")

st.divider()

# =============================================
# MODEL CATALOG - Shows selected models from sidebar
# =============================================
st.markdown("### 📋 Model Catalog & Pricing ($/1M Tokens)")
st.caption(f"Showing {len(st.session_state.allowed_models)} selected models. Use sidebar to change selection.")

# Filter options
col1, col2 = st.columns([1, 3])
with col1:
    show_all_models = st.checkbox("Show all models", value=False)
    sort_by = st.selectbox("Sort by", ["Input Price (Low→High)", "Input Price (High→Low)", "Provider", "Model Name"])

# Build dataframe - show selected models or all
models_to_show = ALL_MODELS if show_all_models else st.session_state.allowed_models
models_data = []
for model_name in models_to_show:
    if model_name in CORTEX_MODELS:
        m = CORTEX_MODELS[model_name]
        # Calculate cost for 1M tokens (input only)
        input_cost_1m = m.input_credits * 3.0  # $3 per credit
        output_cost_1m = m.output_credits * 3.0
        models_data.append({
            "Model": model_name,
            "Provider": m.provider,
            "Category": m.category.title(),
            "Input ($/1M)": input_cost_1m,
            "Output ($/1M)": output_cost_1m,
            "Input (credits/1M)": m.input_credits,
            "Output (credits/1M)": m.output_credits,
            "Context Window": m.context_window,
            "Vision": "✅" if m.supports_vision else "",
            "Selected": "✅" if model_name in st.session_state.allowed_models else "❌"
        })

models_df = pd.DataFrame(models_data)

# Sort
if len(models_df) > 0:
    if sort_by == "Input Price (Low→High)":
        models_df = models_df.sort_values("Input ($/1M)")
    elif sort_by == "Input Price (High→Low)":
        models_df = models_df.sort_values("Input ($/1M)", ascending=False)
    elif sort_by == "Provider":
        models_df = models_df.sort_values("Provider")
    else:
        models_df = models_df.sort_values("Model")

    st.dataframe(
        models_df,
        column_config={
            "Model": st.column_config.TextColumn("Model", width="medium"),
            "Provider": st.column_config.TextColumn("Provider", width="medium"),
            "Category": st.column_config.TextColumn("Tier", width="small"),
            "Input ($/1M)": st.column_config.NumberColumn("Input $/1M", format="$%.2f"),
            "Output ($/1M)": st.column_config.NumberColumn("Output $/1M", format="$%.2f"),
            "Input (credits/1M)": st.column_config.NumberColumn("Input Cr/1M", format="%.2f"),
            "Output (credits/1M)": st.column_config.NumberColumn("Output Cr/1M", format="%.2f"),
            "Context Window": st.column_config.NumberColumn("Context", format="%d"),
            "Vision": st.column_config.TextColumn("Vision", width="small"),
            "Selected": st.column_config.TextColumn("Active", width="small"),
        },
        hide_index=True,
        use_container_width=True
    )

    # Price comparison chart
    st.markdown("##### Price Comparison (Input Tokens - $/1M)")

    chart_df = models_df[["Model", "Input ($/1M)", "Provider"]].copy()
    chart = alt.Chart(chart_df).mark_bar().encode(
        x=alt.X("Model:N", sort=alt.EncodingSortField(field="Input ($/1M)", order="ascending")),
        y=alt.Y("Input ($/1M):Q", title="$ per 1M Input Tokens"),
        color=alt.Color("Provider:N"),
        tooltip=["Model", "Provider", alt.Tooltip("Input ($/1M):Q", format="$,.2f")]
    ).properties(height=300)

    st.altair_chart(chart, use_container_width=True)
else:
    st.warning("No models selected. Use sidebar to select models.")

st.divider()

# =============================================
# QUICK COST CALCULATOR - All Selected Models
# =============================================
st.markdown("### ⚡ Quick Cost Calculator")
st.caption("Calculate costs across ALL selected models")

col1, col2 = st.columns([1, 2])

with col1:
    calc_input_tokens = st.number_input("Input tokens per request", min_value=100, value=1000, step=100)
    calc_output_tokens = st.number_input("Output tokens per request", min_value=10, value=100, step=10)
    calc_num_requests = st.number_input("Number of requests", min_value=1, value=10000, step=1000)
    calc_credit_price = st.number_input("Credit price (USD)", min_value=1.0, value=3.0, step=0.5)

with col2:
    if st.session_state.allowed_models:
        # Calculate costs for ALL selected models
        estimates = []
        for model in st.session_state.allowed_models:
            if model in CORTEX_MODELS:
                total_input = calc_input_tokens * calc_num_requests
                total_output = calc_output_tokens * calc_num_requests
                cost = calculate_cost(model, total_input, total_output, calc_credit_price)
                m = CORTEX_MODELS[model]
                estimates.append({
                    "Model": model,
                    "Provider": m.provider,
                    "Category": m.category.title(),
                    "Total Credits": cost['total_credits'],
                    "Total Cost ($)": cost['total_cost_usd']
                })
        
        estimates_df = pd.DataFrame(estimates).sort_values("Total Cost ($)")
        
        # Find cheapest and most expensive
        if len(estimates_df) > 0:
            cheapest = estimates_df.iloc[0]
            most_expensive = estimates_df.iloc[-1]
            savings = most_expensive['Total Cost ($)'] - cheapest['Total Cost ($)']
            savings_pct = ((most_expensive['Total Cost ($)'] - cheapest['Total Cost ($)']) / most_expensive['Total Cost ($)'] * 100) if most_expensive['Total Cost ($)'] > 0 else 0
            
            # Highlight cheapest and most expensive
            st.markdown("##### 🏆 Cost Comparison Results")
            
            highlight_col1, highlight_col2 = st.columns(2)
            with highlight_col1:
                st.success(f"**💚 CHEAPEST: {cheapest['Model']}**")
                st.metric("Cost", f"${cheapest['Total Cost ($)']:,.2f}", help=f"{cheapest['Total Credits']:,.2f} credits")
            
            with highlight_col2:
                st.error(f"**💸 MOST EXPENSIVE: {most_expensive['Model']}**")
                st.metric("Cost", f"${most_expensive['Total Cost ($)']:,.2f}", help=f"{most_expensive['Total Credits']:,.2f} credits")
            
            st.info(f"**Potential Savings:** ${savings:,.2f} ({savings_pct:.1f}%) by choosing {cheapest['Model']} over {most_expensive['Model']}")
            
            st.markdown("##### Full Cost Breakdown (All Selected Models)")
            
            # Display full table
            st.dataframe(
                estimates_df,
                column_config={
                    "Model": st.column_config.TextColumn("Model", width="medium"),
                    "Provider": st.column_config.TextColumn("Provider", width="medium"),
                    "Category": st.column_config.TextColumn("Tier", width="small"),
                    "Total Credits": st.column_config.NumberColumn("Credits", format="%.2f"),
                    "Total Cost ($)": st.column_config.NumberColumn("Total Cost", format="$%.2f"),
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Summary stats
            st.markdown(f"""
            **Summary for {calc_num_requests:,} requests** ({calc_input_tokens:,} input + {calc_output_tokens:,} output tokens each):
            - **Models compared:** {len(estimates_df)}
            - **Cost range:** ${cheapest['Total Cost ($)']:,.2f} - ${most_expensive['Total Cost ($)']:,.2f}
            - **Max savings:** ${savings:,.2f} ({savings_pct:.1f}%)
            """)
    else:
        st.warning("No models selected. Use sidebar to select models for comparison.")

# =============================================
# FOOTER
# =============================================
st.divider()
st.caption("Cortex AI Cost Simulator v2 | Use sidebar to navigate to Test Workflow or Usage Monitor")
