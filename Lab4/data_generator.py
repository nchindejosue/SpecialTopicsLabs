import numpy as np
import pandas as pd
import os

def generate_software_data(n_samples=1000):
    """
    Generates synthetic software engineering data for defect prediction.
    Features: LOC, Complexity, Code Churn, Team Size
    Target: Defect Risk (0=Low, 1=Medium, 2=High)
    """
    np.random.seed(42)
    
    # Features
    loc = np.random.normal(loc=300, scale=100, size=n_samples)
    loc = np.maximum(loc, 10)
    
    complexity = (loc / 20) + np.random.normal(0, 3, n_samples)
    complexity = np.maximum(complexity, 1)
    
    churn = np.random.exponential(scale=10, size=n_samples)
    
    team_size = np.random.randint(1, 15, size=n_samples)
    
    # Risk Score Calculation
    risk_score = (complexity * 0.5) + (churn * 0.4) + (team_size * 0.1) + np.random.normal(0, 2, n_samples)
    
    # Labels
    labels = []
    for score in risk_score:
        if score < 15: labels.append(0) # Low
        elif score < 25: labels.append(1) # Med
        else: labels.append(2) # High
            
    df = pd.DataFrame({
        'LOC': loc.astype(int),
        'Complexity': complexity.round(1),
        'Code_Churn': churn.round(1),
        'Team_Size': team_size,
        'Defect_Risk': labels
    })
    
    return df

if __name__ == "__main__":
    df = generate_software_data()
    # Save in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "software_metrics.csv")
    df.to_csv(file_path, index=False)
    print(f"Data generated: {file_path}")
