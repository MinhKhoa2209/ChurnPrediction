import csv
import io
from typing import Any, Dict, List


class CSVPrettyPrinter:
    STANDARD_COLUMNS = [
        "customerID",
        "gender",
        "SeniorCitizen",
        "Partner",
        "Dependents",
        "tenure",
        "PhoneService",
        "MultipleLines",
        "InternetService",
        "OnlineSecurity",
        "OnlineBackup",
        "DeviceProtection",
        "TechSupport",
        "StreamingTV",
        "StreamingMovies",
        "Contract",
        "PaperlessBilling",
        "PaymentMethod",
        "MonthlyCharges",
        "TotalCharges",
        "Churn",
    ]

    NUMERIC_COLUMNS = {"MonthlyCharges", "TotalCharges", "Churn_Probability"}

    def __init__(self):
        pass

    def format(self, records: List[Dict[str, Any]], include_probability: bool = False) -> str:
        if not records:
            return ""

        columns = self._determine_columns(records, include_probability)

        output = io.StringIO()
        writer = csv.DictWriter(
            output, fieldnames=columns, quoting=csv.QUOTE_MINIMAL, lineterminator="\n"
        )

        writer.writeheader()

        for record in records:
            formatted_record = self._format_record(record, columns)
            writer.writerow(formatted_record)

        csv_string = output.getvalue()
        output.close()

        return csv_string

    def format_predictions(self, predictions: List[Dict[str, Any]]) -> str:
        records = []
        for pred in predictions:
            record = dict(pred.get("input_features", {}))

            probability = pred.get("probability", 0.0)
            record["Churn_Probability"] = probability

            records.append(record)

        return self.format(records, include_probability=True)

    def _determine_columns(
        self, records: List[Dict[str, Any]], include_probability: bool
    ) -> List[str]:
        if not records:
            return []

        all_keys = set()
        for record in records:
            all_keys.update(record.keys())

        columns = [col for col in self.STANDARD_COLUMNS if col in all_keys]

        if include_probability and "Churn_Probability" in all_keys:
            columns.append("Churn_Probability")

        additional_columns = sorted(all_keys - set(columns) - {"Churn_Probability"})
        columns.extend(additional_columns)

        return columns

    def _format_record(self, record: Dict[str, Any], columns: List[str]) -> Dict[str, str]:
        formatted = {}

        for column in columns:
            value = record.get(column)
            formatted[column] = self._format_value(column, value)

        return formatted

    def _format_value(self, column: str, value: Any) -> str:
        if value is None:
            return ""

        if column in self.NUMERIC_COLUMNS:
            try:
                numeric_value = float(value)
                return f"{numeric_value:.2f}"
            except (ValueError, TypeError):
                return str(value)

        if column == "Churn" and isinstance(value, bool):
            return "Yes" if value else "No"

        if column == "SeniorCitizen" and isinstance(value, (int, bool)):
            return str(int(value))

        if column == "tenure" and isinstance(value, (int, float)):
            return str(int(value))

        return str(value)

    def validate_record(self, record: Dict[str, Any]) -> bool:
        return "customerID" in record and bool(record["customerID"])

    def get_standard_columns(self) -> List[str]:
        return self.STANDARD_COLUMNS.copy()

    def get_numeric_columns(self) -> List[str]:
        return list(self.NUMERIC_COLUMNS)


def format_customer_records(
    records: List[Dict[str, Any]], include_probability: bool = False
) -> str:
    printer = CSVPrettyPrinter()
    return printer.format(records, include_probability=include_probability)


def format_predictions(predictions: List[Dict[str, Any]]) -> str:
    printer = CSVPrettyPrinter()
    return printer.format_predictions(predictions)
