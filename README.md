# 🌾 AgriYield Analytics

### Model Building for Prediction of Mustard Crop Yield Across Districts of Rajasthan

AgriYield Analytics is a data science and machine learning project developed to analyze and predict **mustard crop yield across districts of Rajasthan**.

The project combines data preprocessing, exploratory data analysis, domain-based feature engineering, machine learning, hyperparameter optimization, model interpretation, and an interactive Streamlit dashboard.

---

## 🎯 Project Objective

The primary objective of this project is to build a machine learning model capable of predicting mustard crop yield using agricultural, environmental, soil, water, and management-related factors.

The project focuses on understanding how factors such as:

- Irrigation method
- Soil type
- Season
- Nutrient availability
- Water availability and consumption
- Rainfall
- Temperature
- Humidity
- Production

relate to mustard crop yield across Rajasthan.

---

## 📊 Dataset

The primary Rajasthan Mustard Crop dataset contains:

- **25,000 records**
- **19 features**
- Numerical and categorical agricultural variables
- Mustard crop yield as the target variable

The dataset was checked for missing values and found to contain **zero missing values across all 25,000 records**, so no imputation was required.

### Dataset Categories

The project includes information related to:

- District
- Crop
- Season
- Area
- Production
- Yield
- Rainfall
- Soil type
- pH level
- Organic matter
- Nitrogen
- Phosphorus
- Potassium
- Temperature
- Humidity
- Wind speed
- Irrigation method
- Water availability
- Water consumption

---

# 🔬 Data Science Workflow

The project follows the following workflow:

```text
Raw Agricultural Data
        │
        ▼
Missing Value Analysis
        │
        ▼
Distribution Analysis
        │
        ▼
Categorical Balance Check
        │
        ▼
Correlation Analysis
        │
        ▼
Feature Engineering
        │
        ▼
Feature Transformation
        │
        ▼
Categorical Encoding
        │
        ▼
Train / Test Split
        │
        ▼
Model Benchmarking
        │
        ▼
Hyperparameter Tuning
        │
        ▼
Model Evaluation
        │
        ▼
SHAP & Interpretability Analysis
        │
        ▼
Interactive Streamlit Dashboard
