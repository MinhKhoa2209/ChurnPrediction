from utils.csv_printer import CSVPrettyPrinter, format_predictions

printer = CSVPrettyPrinter()


customer_records = [
    {
        "customerID": "7590-VHVEG",
        "gender": "Female",
        "SeniorCitizen": 0,
        "Partner": "Yes",
        "Dependents": "No",
        "tenure": 1,
        "PhoneService": "No",
        "MultipleLines": "No phone service",
        "InternetService": "DSL",
        "OnlineSecurity": "No",
        "OnlineBackup": "Yes",
        "DeviceProtection": "No",
        "TechSupport": "No",
        "StreamingTV": "No",
        "StreamingMovies": "No",
        "Contract": "Month-to-month",
        "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check",
        "MonthlyCharges": 29.85,
        "TotalCharges": 29.85,
        "Churn": "No",
    },
    {
        "customerID": "5575-GNVDE",
        "gender": "Male",
        "SeniorCitizen": 0,
        "Partner": "No",
        "Dependents": "No",
        "tenure": 34,
        "PhoneService": "Yes",
        "MultipleLines": "No",
        "InternetService": "DSL",
        "OnlineSecurity": "Yes",
        "OnlineBackup": "No",
        "DeviceProtection": "Yes",
        "TechSupport": "No",
        "StreamingTV": "No",
        "StreamingMovies": "No",
        "Contract": "One year",
        "PaperlessBilling": "No",
        "PaymentMethod": "Mailed check",
        "MonthlyCharges": 56.95,
        "TotalCharges": 1889.5,
        "Churn": "No",
    },
]

print("=" * 80)
print("CSV Pretty Printer Demonstration")
print("=" * 80)
print()


print("1. Format customer records (without probability):")
print("-" * 80)
csv_output = printer.format(customer_records)
print(csv_output)
print()


print("2. Format customer records (with probability):")
print("-" * 80)
records_with_prob = [
    {**customer_records[0], "Churn_Probability": 0.234567},
    {**customer_records[1], "Churn_Probability": 0.123456},
]
csv_output_with_prob = printer.format(records_with_prob, include_probability=True)
print(csv_output_with_prob)
print()


print("3. Format predictions:")
print("-" * 80)
predictions = [
    {"input_features": customer_records[0], "probability": 0.234567},
    {"input_features": customer_records[1], "probability": 0.123456},
]
csv_predictions = format_predictions(predictions)
print(csv_predictions)
print()


print("4. Numeric formatting (2 decimal places):")
print("-" * 80)
test_record = {
    "customerID": "TEST-001",
    "gender": "Male",
    "tenure": 12,
    "MonthlyCharges": 50.5,
    "TotalCharges": 606.0,
    "Churn": "No",
    "Churn_Probability": 0.234567,
}
csv_numeric = printer.format([test_record], include_probability=True)
print(csv_numeric)
print()


print("5. RFC 4180 compliance (special characters):")
print("-" * 80)
special_records = [
    {
        "customerID": "TEST,001",
        "gender": "Male",
        "tenure": 12,
        "Contract": "Month-to-month",
        "PaymentMethod": "Bank transfer (automatic)",
        "MonthlyCharges": 50.00,
        "TotalCharges": 600.00,
        "Churn": "No",
    },
    {
        "customerID": 'TEST"002',
        "gender": "Female",
        "tenure": 24,
        "Contract": "One year",
        "PaymentMethod": "Credit card",
        "MonthlyCharges": 75.00,
        "TotalCharges": 1800.00,
        "Churn": "Yes",
    },
]
csv_special = printer.format(special_records)
print(csv_special)
print()

print("=" * 80)
print("Demonstration complete!")
print("=" * 80)
