import streamlit as st
import json
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def load_data(file_path):
    """Load the JSON data from the specified file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def create_dataframe(data):
    """Convert the JSON data to a pandas DataFrame for easier analysis."""
    rows = []
    for model_name, results in data.items():
        for result in results:
            rows.append({
                'model': model_name,
                'correct_chunk_id': result['correct_chunk_id'],
                'returned_chunk_id': result['returned_chunk_id'],
                'search_query': result['search_query'],
                'correct_chunk_code': result['correct_chunk_code'],
                'wrong_chunk_code': result['wrong_chunk_code'],
                'is_correct_match': result['correct_chunk_id'] == result['returned_chunk_id']
            })
    return pd.DataFrame(rows)

def calculate_metrics(df):
    """Calculate various metrics for the embedding model performance."""
    total_queries = len(df)
    correct_matches = df['is_correct_match'].sum()
    accuracy = (correct_matches / total_queries) * 100 if total_queries > 0 else 0
    
    # Calculate code length statistics
    df['correct_code_length'] = df['correct_chunk_code'].str.len()
    df['wrong_code_length'] = df['wrong_chunk_code'].str.len()
    df['query_length'] = df['search_query'].str.len()
    
    return {
        'total_queries': total_queries,
        'correct_matches': correct_matches,
        'accuracy': accuracy,
        'avg_correct_code_length': df['correct_code_length'].mean(),
        'avg_wrong_code_length': df['wrong_code_length'].mean(),
        'avg_query_length': df['query_length'].mean()
    }

def main():
    st.set_page_config(
        page_title="Embedding Model Evaluation Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🔍 Embedding Model Evaluation Dashboard")
    st.markdown("Visualization of embedding model search result accuracy")
    
    # File upload or default path
    data_file = Path("/home/mokt/dev/django-rag/django_knowledge/bad_results.json")
    
    if not data_file.exists():
        st.error(f"Data file not found: {data_file}")
        return
    
    # Load data
    with st.spinner("Loading data..."):
        raw_data = load_data(data_file)
        if raw_data is None:
            return
        
        df = create_dataframe(raw_data)
        metrics = calculate_metrics(df)
    
    # Sidebar for model selection
    st.sidebar.header("📈 Model Performance")
    
    # Display overall metrics
    st.sidebar.metric("Total Queries", metrics['total_queries'])
    st.sidebar.metric("Correct Matches", metrics['correct_matches'])
    st.sidebar.metric("Accuracy", f"{metrics['accuracy']:.1f}%")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔍 Detailed Analysis", "📝 Code Comparison", "📈 Statistics"])
    
    with tab1:
        st.header("Performance Overview")
        
        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Queries", metrics['total_queries'])
        
        with col2:
            st.metric("Correct Matches", metrics['correct_matches'])
        
        with col3:
            st.metric("Accuracy", f"{metrics['accuracy']:.1f}%")
        
        with col4:
            st.metric("Avg Query Length", f"{metrics['avg_query_length']:.0f} chars")
        
        # Accuracy gauge chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = metrics['accuracy'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Model Accuracy (%)"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Correct vs Incorrect matches pie chart
        correct_count = metrics['correct_matches']
        incorrect_count = metrics['total_queries'] - correct_count
        
        fig_pie = px.pie(
            values=[correct_count, incorrect_count],
            names=['Correct Matches', 'Incorrect Matches'],
            title="Search Result Distribution",
            color_discrete_map={'Correct Matches': 'green', 'Incorrect Matches': 'red'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with tab2:
        st.header("Detailed Query Analysis")
        
        # Search and filter
        search_query = st.text_input("Search in queries:", "")
        
        filtered_df = df.copy()
        if search_query:
            filtered_df = filtered_df[filtered_df['search_query'].str.contains(search_query, case=False, na=False)]
        
        # Filter by correctness
        filter_option = st.selectbox("Filter by result:", ["All", "Correct matches only", "Incorrect matches only"])
        
        if filter_option == "Correct matches only":
            filtered_df = filtered_df[filtered_df['is_correct_match']]
        elif filter_option == "Incorrect matches only":
            filtered_df = filtered_df[~filtered_df['is_correct_match']]
        
        st.write(f"Showing {len(filtered_df)} of {len(df)} results")
        
        # Display results in expandable format
        for idx, row in filtered_df.iterrows():
            with st.expander(f"Query {idx + 1}: {row['search_query']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🎯 Correct Result")
                    st.write(f"Chunk ID: {row['correct_chunk_id']}")
                    st.code(row['correct_chunk_code'], language='python')
                    
                with col2:
                    st.subheader("❌ Returned Result" if not row['is_correct_match'] else "✅ Returned Result")
                    st.write(f"Chunk ID: {row['returned_chunk_id']}")
                    st.code(row['wrong_chunk_code'], language='python')
                    
                # Match status
                if row['is_correct_match']:
                    st.success("✅ Correct match!")
                else:
                    st.error("❌ Incorrect match")
    
    with tab3:
        st.header("Code Length Analysis")
        
        # Create scatter plot of code lengths
        fig_scatter = px.scatter(
            df,
            x='correct_code_length',
            y='wrong_code_length',
            color='is_correct_match',
            title="Code Length Comparison",
            labels={
                'correct_code_length': 'Correct Code Length (chars)',
                'wrong_code_length': 'Returned Code Length (chars)',
                'is_correct_match': 'Match Correctness'
            },
            color_discrete_map={True: 'green', False: 'red'}
        )
        
        # Add diagonal line for perfect match
        fig_scatter.add_shape(
            type='line',
            x0=df['correct_code_length'].min(),
            y0=df['correct_code_length'].min(),
            x1=df['correct_code_length'].max(),
            y1=df['correct_code_length'].max(),
            line=dict(color='blue', width=2, dash='dash'),
            name="Perfect Match Line"
        )
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Length distribution histograms
        fig_hist = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Correct Code Length', 'Wrong Code Length', 'Query Length', 'Length Difference'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        fig_hist.add_trace(
            go.Histogram(x=df['correct_code_length'], name='Correct Code', marker_color='green'),
            row=1, col=1
        )
        
        fig_hist.add_trace(
            go.Histogram(x=df['wrong_code_length'], name='Wrong Code', marker_color='red'),
            row=1, col=2
        )
        
        fig_hist.add_trace(
            go.Histogram(x=df['query_length'], name='Query Length', marker_color='blue'),
            row=2, col=1
        )
        
        df['length_diff'] = df['correct_code_length'] - df['wrong_code_length']
        fig_hist.add_trace(
            go.Histogram(x=df['length_diff'], name='Length Difference', marker_color='orange'),
            row=2, col=2
        )
        
        fig_hist.update_layout(height=600, showlegend=False, title_text="Length Distributions")
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with tab4:
        st.header("Statistical Summary")
        
        # Create summary statistics table
        stats_df = pd.DataFrame({
            'Metric': [
                'Total Queries',
                'Correct Matches',
                'Incorrect Matches',
                'Accuracy (%)',
                'Avg Correct Code Length',
                'Avg Wrong Code Length',
                'Avg Query Length',
                'Min Correct Code Length',
                'Max Correct Code Length',
                'Min Wrong Code Length',
                'Max Wrong Code Length'
            ],
            'Value': [
                metrics['total_queries'],
                metrics['correct_matches'],
                metrics['total_queries'] - metrics['correct_matches'],
                f"{metrics['accuracy']:.2f}",
                f"{metrics['avg_correct_code_length']:.0f}",
                f"{metrics['avg_wrong_code_length']:.0f}",
                f"{metrics['avg_query_length']:.0f}",
                f"{df['correct_code_length'].min():.0f}",
                f"{df['correct_code_length'].max():.0f}",
                f"{df['wrong_code_length'].min():.0f}",
                f"{df['wrong_code_length'].max():.0f}"
            ]
        })
        
        st.dataframe(stats_df, use_container_width=True)
        
        # Model information
        st.subheader("Model Information")
        model_name = list(raw_data.keys())[0] if raw_data else "Unknown"
        st.write(f"**Model:** {model_name}")
        st.write(f"**Total Evaluation Results:** {len(raw_data[model_name]) if raw_data else 0}")

if __name__ == "__main__":
    main()
