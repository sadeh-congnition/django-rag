import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

st.set_page_config(
    page_title="RAG Evaluations Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 RAG Evaluations Dashboard")
st.markdown("Visualizing evaluation results from the Django RAG system")

# API endpoint
API_URL = "http://127.0.0.1:8000/api/evaluations"

@st.cache_data(ttl=60)  # Cache for 60 seconds
def fetch_evaluations():
    """Fetch evaluation data from the API"""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return None

def format_timestamp(timestamp_str):
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return timestamp_str

# Main content
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()

# Fetch data
evaluations = fetch_evaluations()

if evaluations is None:
    st.error("❌ Could not fetch evaluation data. Make sure the Django server is running on http://127.0.0.1:8000")
    st.stop()

if not evaluations:
    st.info("📝 No evaluation data available")
    st.stop()

# Sidebar for filters
st.sidebar.header("🔍 Filters")

# Extract unique values for filters
embedding_models = list(set(eval['embedding_model']['name'] for eval in evaluations))
selected_models = st.sidebar.multiselect(
    "Embedding Models", 
    embedding_models, 
    default=embedding_models
)

# Filter evaluations
filtered_evals = [
    eval for eval in evaluations 
    if eval['embedding_model']['name'] in selected_models
]

# Main dashboard
st.header("📈 Overview Metrics")

col1, col2, col3, col4 = st.columns(4)

total_evals = len(filtered_evals)
avg_score = sum(eval['score'] for eval in filtered_evals) / total_evals if total_evals > 0 else 0
avg_percentage = sum(eval['score_percentage'] for eval in filtered_evals) / total_evals if total_evals > 0 else 0

with col1:
    st.metric("Total Evaluations", total_evals)

with col2:
    st.metric("Average Score", f"{avg_score:.2f}")

with col3:
    st.metric("Average Percentage", f"{avg_percentage:.1f}%")

with col4:
    st.metric("Models Tested", len(selected_models))

# Create DataFrame for easier plotting
df = pd.DataFrame(filtered_evals)
df['created_at'] = pd.to_datetime(df['created_at'])
df['model_name'] = df['embedding_model'].apply(lambda x: x['name'])

# Charts section
st.header("📊 Visualizations")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Scores by Model")
    fig_scores = px.box(
        df, 
        x='model_name', 
        y='score',
        title="Score Distribution by Embedding Model",
        color='model_name'
    )
    fig_scores.update_layout(showlegend=False)
    st.plotly_chart(fig_scores, use_container_width=True)

with col2:
    st.subheader("Score Percentages")
    fig_percentage = px.bar(
        df.sort_values('created_at', ascending=False).head(10),
        x='name',
        y='score_percentage',
        title="Recent Evaluations - Score Percentages",
        color='model_name'
    )
    fig_percentage.update_xaxes(tickangle=45)
    st.plotly_chart(fig_percentage, use_container_width=True)

# Performance metrics
st.header("⚡ Performance Analysis")

# Extract performance data
performance_data = []
for eval in filtered_evals:
    if eval.get('embedder_performance'):
        perf = eval['embedder_performance']
        performance_data.append({
            'evaluation_name': eval['name'],
            'model_name': eval['embedding_model']['name'],
            'search_time': perf['search_time'],
            'embedding_time': perf['embedding_time'],
            'total_time': perf['search_time'] + perf['embedding_time']
        })

if performance_data:
    perf_df = pd.DataFrame(performance_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Search Time by Model")
        fig_search = px.scatter(
            perf_df,
            x='evaluation_name',
            y='search_time',
            color='model_name',
            title="Search Time Comparison",
            size='total_time'
        )
        fig_search.update_xaxes(tickangle=45)
        st.plotly_chart(fig_search, use_container_width=True)
    
    with col2:
        st.subheader("Embedding Time by Model")
        # Aggregate by model and take maximum embedding time
        max_embed_df = perf_df.groupby('model_name')['embedding_time'].max().reset_index()
        max_embed_df = max_embed_df.sort_values('embedding_time', ascending=False)
        
        fig_embed = px.bar(
            max_embed_df,
            x='model_name',
            y='embedding_time',
            title="Maximum Embedding Time by Model",
            color='model_name'
        )
        fig_embed.update_xaxes(tickangle=45)
        fig_embed.update_layout(showlegend=False)
        st.plotly_chart(fig_embed, use_container_width=True)

# Timeline view
st.header("📅 Timeline View")

fig_timeline = px.line(
    df.sort_values('created_at'),
    x='created_at',
    y='score_percentage',
    color='model_name',
    title="Score Percentage Over Time",
    markers=True,
    hover_data=['name', 'description']
)
st.plotly_chart(fig_timeline, use_container_width=True)

# Detailed data table
st.header("📋 Detailed Evaluation Data")

# Format data for display
display_data = []
for eval in filtered_evals:
    display_data.append({
        'ID': eval['id'],
        'Name': eval['name'],
        'Model': eval['embedding_model']['name'],
        'Score': eval['score'],
        'Percentage': f"{eval['score_percentage']}%",
        'Description': eval['description'][:100] + "..." if len(eval['description']) > 100 else eval['description'],
        'Created': format_timestamp(eval['created_at'])
    })

display_df = pd.DataFrame(display_data)
st.dataframe(display_df, use_container_width=True)

# Raw JSON viewer (collapsible)
with st.expander("🔧 View Raw JSON Data"):
    st.json(evaluations)

# Footer
st.markdown("---")
st.markdown("📊 Dashboard powered by Streamlit | Data from Django RAG Evaluation API")