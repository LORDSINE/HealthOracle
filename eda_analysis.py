"""EDA Analysis Backend - Processes and returns analysis results."""

import pandas as pd
import numpy as np
import os
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import chi2_contingency, mannwhitneyu, pointbiserialr
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)

# Load dataset
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'health_data_clean(1).csv')

def load_data():
    """Load the dataset."""
    return pd.read_csv(DATA_PATH)

def fig_to_base64(fig):
    """Convert matplotlib figure to base64 string."""
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f'data:image/png;base64,{img_str}'

def get_dataset_overview():
    """Get basic dataset statistics."""
    df = load_data()
    return {
        'total_records': len(df),
        'features': len(df.columns),
        'missing_values': int(df.isnull().sum().sum()),
        'target_variable': 'HeartDiseaseorAttack',
        'duplicates': int(df.duplicated().sum())
    }

def analyze_target_distribution():
    """Analyze target variable distribution with multiple plots."""
    df = load_data()
    target_counts = df['HeartDiseaseorAttack'].value_counts()
    target_pct = (target_counts / len(df) * 100).round(2)
    
    # Create figure with 3 subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # Count Plot
    sns.countplot(data=df, x='HeartDiseaseorAttack', palette='Set2', ax=axes[0])
    axes[0].set_title('Heart Disease Distribution (Count)', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Heart Disease (0=No, 1=Yes)')
    axes[0].set_ylabel('Count')
    for p in axes[0].patches:
        axes[0].annotate(f'{int(p.get_height()):,}',
                        (p.get_x() + p.get_width() / 2., p.get_height()),
                        ha='center', va='bottom', fontsize=11)
    
    # Pie Chart
    colors = ['#90EE90', '#FF6B6B']
    axes[1].pie(target_counts, labels=['No Disease', 'Disease'], autopct='%1.1f%%',
                colors=colors, startangle=90, explode=(0, 0.1))
    axes[1].set_title('Target Variable Proportion', fontsize=14, fontweight='bold')
    
    # Bar Chart with Percentages
    target_pct.plot(kind='bar', color=colors, ax=axes[2], alpha=0.7)
    axes[2].set_title('Percentage Distribution', fontsize=14, fontweight='bold')
    axes[2].set_xlabel('Heart Disease')
    axes[2].set_ylabel('Percentage (%)')
    axes[2].set_xticklabels(['No Disease', 'Disease'], rotation=0)
    for i, v in enumerate(target_pct):
        axes[2].text(i, v + 2, f'{v:.2f}%', ha='center', fontweight='bold')
    
    plt.tight_layout()
    
    return {
        'stats': {
            'no_disease': int(target_counts[0]),
            'disease': int(target_counts[1]),
            'no_disease_pct': float(target_pct[0]),
            'disease_pct': float(target_pct[1]),
            'imbalance_ratio': round(target_counts[0] / target_counts[1], 2)
        },
        'chart': fig_to_base64(fig)
    }

def analyze_numerical_features():
    """
    Professional Numerical Features Analysis with 5 sections:
    1. Statistical Summary Table
    2. Distribution Plots (Histogram + KDE) for continuous features
    3. Outlier Detection (Boxplots)
    4. Numerical Features vs Target (Violin plots)
    5. Correlation with Target (Bar chart)
    """
    df = load_data()
    
    # Define feature categories
    continuous_cols = ['BMI', 'Age', 'GenHlth', 'MentHlth', 'PhysHlth', 'Education', 'Income']
    distribution_cols = ['BMI', 'Age', 'GenHlth']  # Best picks for distribution plots
    outlier_cols = ['BMI', 'MentHlth', 'PhysHlth']  # For boxplot outlier detection
    vs_target_cols = ['BMI', 'Age', 'GenHlth']  # For violin plots vs target
    
    # =========================================================================
    # SECTION 1: Statistical Summary Table
    # =========================================================================
    stats_summary = []
    for col in continuous_cols:
        if col in df.columns:
            stats_summary.append({
                'feature': col,
                'mean': float(round(df[col].mean(), 2)),
                'median': float(round(df[col].median(), 2)),
                'std': float(round(df[col].std(), 2)),
                'min': float(round(df[col].min(), 2)),
                'max': float(round(df[col].max(), 2)),
                'skewness': float(round(df[col].skew(), 2)),
                'kurtosis': float(round(df[col].kurtosis(), 2))
            })
    
    # =========================================================================
    # SECTION 2: Distribution Plots (Histogram + KDE)
    # =========================================================================
    fig1, axes = plt.subplots(1, 3, figsize=(16, 5))
    colors = ['#3B82F6', '#10B981', '#F59E0B']
    
    for idx, col in enumerate(distribution_cols):
        if col in df.columns:
            sns.histplot(df[col], kde=True, ax=axes[idx], color=colors[idx], bins=30, alpha=0.7)
            
            # Add mean and median lines
            mean_val = df[col].mean()
            median_val = df[col].median()
            axes[idx].axvline(mean_val, color='#EF4444', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f}')
            axes[idx].axvline(median_val, color='#22C55E', linestyle='-', linewidth=2, label=f'Median: {median_val:.1f}')
            
            axes[idx].set_title(f'Distribution of {col}', fontsize=13, fontweight='bold', pad=12)
            axes[idx].set_xlabel(col, fontsize=11)
            axes[idx].set_ylabel('Frequency', fontsize=11)
            axes[idx].legend(loc='upper right', fontsize=9)
            axes[idx].tick_params(labelsize=10)
    
    plt.suptitle('Distribution Analysis of Key Numerical Features', fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    chart_distribution = fig_to_base64(fig1)
    
    # =========================================================================
    # SECTION 3: Outlier Detection (Boxplots)
    # =========================================================================
    fig2, axes = plt.subplots(1, 3, figsize=(14, 5))
    box_colors = ['#8B5CF6', '#EC4899', '#06B6D4']
    
    for idx, col in enumerate(outlier_cols):
        if col in df.columns:
            bp = axes[idx].boxplot(df[col].dropna(), patch_artist=True, widths=0.6)
            bp['boxes'][0].set_facecolor(box_colors[idx])
            bp['boxes'][0].set_alpha(0.7)
            bp['medians'][0].set_color('#1F2937')
            bp['medians'][0].set_linewidth(2)
            
            # Count outliers
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)][col]
            outlier_pct = len(outliers) / len(df) * 100
            
            axes[idx].set_title(f'{col}\n({outlier_pct:.1f}% outliers)', fontsize=12, fontweight='bold')
            axes[idx].set_ylabel(col, fontsize=11)
            axes[idx].tick_params(labelsize=10)
            axes[idx].set_xticklabels([''])
    
    plt.suptitle('Outlier Detection using Boxplots', fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    chart_outliers = fig_to_base64(fig2)
    
    # =========================================================================
    # SECTION 4: Numerical Features vs Target (Violin Plots)
    # =========================================================================
    fig3, axes = plt.subplots(1, 3, figsize=(16, 6))
    
    for idx, col in enumerate(vs_target_cols):
        if col in df.columns:
            sns.violinplot(data=df, x='HeartDiseaseorAttack', y=col, 
                          palette=['#90EE90', '#FF6B6B'], ax=axes[idx], inner='box')
            axes[idx].set_title(f'{col} vs Heart Disease', fontsize=13, fontweight='bold', pad=12)
            axes[idx].set_xlabel('Heart Disease (0=No, 1=Yes)', fontsize=11)
            axes[idx].set_ylabel(col, fontsize=11)
            axes[idx].set_xticklabels(['No Disease', 'Has Disease'], fontsize=10)
            axes[idx].tick_params(labelsize=10)
    
    plt.suptitle('Numerical Features vs Heart Disease (Violin Plots)', fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    chart_vs_target = fig_to_base64(fig3)
    
    # =========================================================================
    # SECTION 5: Correlation with Target (Bar Chart)
    # =========================================================================
    # Calculate correlations with target
    all_numerical = ['BMI', 'Age', 'GenHlth', 'MentHlth', 'PhysHlth', 'Education', 'Income',
                     'HighBP', 'HighChol', 'Smoker', 'PhysActivity', 'DiffWalk', 'Diabetes_binary']
    
    correlations = []
    for col in all_numerical:
        if col in df.columns:
            corr = df[col].corr(df['HeartDiseaseorAttack'])
            correlations.append({'feature': col, 'correlation': float(round(corr, 4))})
    
    # Sort by absolute correlation
    correlations = sorted(correlations, key=lambda x: abs(x['correlation']), reverse=True)
    
    # Create bar chart
    fig4, ax = plt.subplots(figsize=(12, 6))
    features = [c['feature'] for c in correlations]
    corr_values = [c['correlation'] for c in correlations]
    colors = ['#EF4444' if v > 0 else '#22C55E' for v in corr_values]
    
    bars = ax.barh(features, corr_values, color=colors, alpha=0.8, edgecolor='#1F2937', linewidth=0.5)
    ax.axvline(x=0, color='#1F2937', linewidth=1)
    ax.set_xlabel('Correlation Coefficient', fontsize=12)
    ax.set_ylabel('Features', fontsize=12)
    ax.set_title('Correlation of Numerical Features with Heart Disease', fontsize=14, fontweight='bold', pad=15)
    ax.tick_params(labelsize=10)
    
    # Add correlation values on bars
    for bar, val in zip(bars, corr_values):
        width = bar.get_width()
        ax.text(width + 0.01 if width >= 0 else width - 0.04, bar.get_y() + bar.get_height()/2,
                f'{val:.3f}', va='center', fontsize=9, fontweight='bold')
    
    ax.invert_yaxis()  # Highest correlation at top
    plt.tight_layout()
    chart_correlation = fig_to_base64(fig4)
    
    return {
        'stats_summary': stats_summary,
        'correlations': correlations,
        'charts': {
            'distribution': chart_distribution,
            'outliers': chart_outliers,
            'vs_target': chart_vs_target,
            'correlation': chart_correlation
        }
    }

def analyze_categorical_features():
    """Analyze categorical/binary features with bar charts."""
    df = load_data()
    binary_cols = ['HighBP', 'HighChol', 'Smoker', 'PhysActivity', 'DiffWalk', 'Sex']
    
    # Count and percentage
    fig1, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.ravel()
    
    for idx, col in enumerate(binary_cols):
        counts = df[col].value_counts()
        pct = df[col].value_counts(normalize=True) * 100
        
        # Bar plot
        sns.countplot(data=df, x=col, palette='viridis', ax=axes[idx])
        axes[idx].set_title(f'{col} Distribution', fontsize=11, fontweight='bold')
        axes[idx].set_xlabel(f'{col} (0=No, 1=Yes)')
        axes[idx].set_ylabel('Count')
        
        # Add percentages
        for p in axes[idx].patches:
            height = p.get_height()
            axes[idx].text(p.get_x() + p.get_width()/2., height,
                          f'{height:,.0f}\n({height/len(df)*100:.1f}%)',
                          ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    chart1 = fig_to_base64(fig1)
    
    # Stacked bar charts vs target
    fig2, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.ravel()
    
    for idx, col in enumerate(binary_cols):
        # Cross-tabulation
        ct = pd.crosstab(df[col], df['HeartDiseaseorAttack'], normalize='index') * 100
        ct.plot(kind='bar', stacked=False, ax=axes[idx], color=['#90EE90', '#FF6B6B'], alpha=0.8)
        axes[idx].set_title(f'{col} vs Heart Disease', fontsize=11, fontweight='bold')
        axes[idx].set_xlabel(f'{col} (0=No, 1=Yes)')
        axes[idx].set_ylabel('Percentage (%)')
        axes[idx].legend(['No Disease', 'Disease'], loc='upper right')
        axes[idx].set_xticklabels(axes[idx].get_xticklabels(), rotation=0)
    
    plt.tight_layout()
    chart2 = fig_to_base64(fig2)
    
    # Create data for statistics
    data = []
    for col in binary_cols:
        counts = df[col].value_counts()
        pct = (counts / len(df) * 100).round(2)
        data.append({
            'feature': col,
            'no_count': int(counts.get(0, 0)),
            'yes_count': int(counts.get(1, 0)),
            'no_pct': float(pct.get(0, 0)),
            'yes_pct': float(pct.get(1, 0))
        })
    
    return {
        'stats': data,
        'charts': [chart1, chart2]
    }

def analyze_correlations():
    """Analyze feature correlations with heatmap and bar charts."""
    df = load_data()
    corr_features = ['HeartDiseaseorAttack', 'HighBP', 'HighChol', 'BMI', 'Smoker',
                     'PhysActivity', 'DiffWalk', 'Sex', 'Age', 'GenHlth', 'MentHlth', 'PhysHlth']
    
    corr_matrix = df[corr_features].corr()
    
    # Create heatmap
    fig1, ax = plt.subplots(figsize=(14, 12))
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax)
    ax.set_title('Correlation Matrix - All Features', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    chart1 = fig_to_base64(fig1)
    
    # Top correlations with target
    target_corr = corr_matrix['HeartDiseaseorAttack'].drop('HeartDiseaseorAttack').sort_values(ascending=False)
    
    # Visualize top correlations
    fig2, axes = plt.subplots(1, 2, figsize=(18, 6))
    
    # Top positive correlations
    top_pos = target_corr.head(10)
    top_pos.plot(kind='barh', ax=axes[0], color='crimson', alpha=0.7)
    axes[0].set_title('Top 10 Positive Correlations with Heart Disease', fontsize=13, fontweight='bold')
    axes[0].set_xlabel('Correlation Coefficient')
    axes[0].axvline(0, color='black', linestyle='--', linewidth=0.8)
    
    # Top negative correlations
    top_neg = target_corr.tail(10)
    top_neg.plot(kind='barh', ax=axes[1], color='steelblue', alpha=0.7)
    axes[1].set_title('Top 10 Negative Correlations with Heart Disease', fontsize=13, fontweight='bold')
    axes[1].set_xlabel('Correlation Coefficient')
    axes[1].axvline(0, color='black', linestyle='--', linewidth=0.8)
    
    plt.tight_layout()
    chart2 = fig_to_base64(fig2)
    
    # Pairplot for key features (sample data)
    key_features = ['BMI', 'Age', 'GenHlth', 'PhysHlth', 'HeartDiseaseorAttack']
    df_sample = df[key_features].sample(n=min(3000, len(df)), random_state=42)
    
    pair_fig = sns.pairplot(df_sample, hue='HeartDiseaseorAttack', palette='Set1',
                            diag_kind='kde', plot_kws={'alpha': 0.6})
    pair_fig.fig.suptitle('Pairplot: Key Features vs Heart Disease', y=1.02, fontsize=16, fontweight='bold')
    plt.tight_layout()
    chart3 = fig_to_base64(pair_fig.fig)
    
    return {
        'top_correlations': {
            'features': target_corr.index.tolist(),
            'values': target_corr.values.round(4).tolist()
        },
        'charts': [chart1, chart2, chart3]
    }

def analyze_risk_factors():
    """Analyze multiple risk factors with visualizations."""
    df = load_data()
    risk_cols = ['HighBP', 'HighChol', 'Smoker']
    
    df['RiskFactorCount'] = df[risk_cols].sum(axis=1)
    risk_analysis = df.groupby('RiskFactorCount').agg({
        'HeartDiseaseorAttack': ['mean', 'count']
    }).reset_index()
    risk_analysis.columns = ['RiskFactorCount', 'DiseaseRate', 'Count']
    risk_analysis['DiseaseRate'] = (risk_analysis['DiseaseRate'] * 100).round(2)
    
    # Create visualization
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    axes[0].bar(risk_analysis['RiskFactorCount'], risk_analysis['DiseaseRate'],
                color='coral', alpha=0.7, edgecolor='black')
    axes[0].set_title('Heart Disease Rate by Number of Risk Factors', fontsize=13, fontweight='bold')
    axes[0].set_xlabel('Number of Risk Factors')
    axes[0].set_ylabel('Disease Rate (%)')
    axes[0].grid(axis='y', alpha=0.3)
    
    # Add values on bars
    for i, (x, y) in enumerate(zip(risk_analysis['RiskFactorCount'], risk_analysis['DiseaseRate'])):
        axes[0].text(x, y + 1, f'{y:.1f}%', ha='center', fontweight='bold')
    
    axes[1].bar(risk_analysis['RiskFactorCount'], risk_analysis['Count'],
                color='steelblue', alpha=0.7, edgecolor='black')
    axes[1].set_title('Sample Distribution by Number of Risk Factors', fontsize=13, fontweight='bold')
    axes[1].set_xlabel('Number of Risk Factors')
    axes[1].set_ylabel('Count')
    axes[1].grid(axis='y', alpha=0.3)
    
    # Add values on bars
    for i, (x, y) in enumerate(zip(risk_analysis['RiskFactorCount'], risk_analysis['Count'])):
        axes[1].text(x, y + 500, f'{y:,}', ha='center', fontweight='bold')
    
    plt.tight_layout()
    
    return {
        'stats': risk_analysis.to_dict('records'),
        'chart': fig_to_base64(fig)
    }

def analyze_statistical_tests():
    """Perform statistical tests with visualizations."""
    df = load_data()
    binary_cols = ['HighBP', 'HighChol', 'Smoker', 'PhysActivity', 'DiffWalk', 'Sex']
    
    chi_results = []
    for col in binary_cols:
        contingency_table = pd.crosstab(df[col], df['HeartDiseaseorAttack'])
        chi2, p_value, dof, expected = chi2_contingency(contingency_table)
        
        # Cramér's V (effect size)
        n = contingency_table.sum().sum()
        cramers_v = np.sqrt(chi2 / (n * (min(contingency_table.shape) - 1)))
        
        chi_results.append({
            'feature': col,
            'chi2': round(chi2, 2),
            'p_value': f'{p_value:.6f}',
            'cramers_v': round(cramers_v, 4),
            'significant': 'Yes ✓' if p_value < 0.05 else 'No ✗'
        })
    
    # Create visualization
    features = [r['feature'] for r in chi_results]
    cramers_v_values = [r['cramers_v'] for r in chi_results]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(features, cramers_v_values, color='steelblue', alpha=0.7, edgecolor='black')
    ax.set_title("Cramér's V - Effect Size (Feature Association with Heart Disease)", 
                 fontsize=14, fontweight='bold')
    ax.set_xlabel("Cramér's V", fontsize=12)
    ax.set_ylabel('Feature', fontsize=12)
    ax.grid(axis='x', alpha=0.3)
    
    # Add values on bars
    for bar, value in zip(bars, cramers_v_values):
        width = bar.get_width()
        ax.text(width + 0.005, bar.get_y() + bar.get_height()/2, 
                f'{value:.4f}', ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()
    
    return {
        'chi_square_tests': chi_results,
        'chart': fig_to_base64(fig)
    }
