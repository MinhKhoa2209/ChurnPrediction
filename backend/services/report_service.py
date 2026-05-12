import io
import logging
import time
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from backend.domain.models.customer_record import CustomerRecord
from backend.domain.models.model_version import ModelVersion
from backend.domain.models.report import Report
from backend.infrastructure.storage import storage_client
from backend.services.ml_training_service import MLTrainingService
from backend.services.model_evaluation_service import ModelEvaluationService

logger = logging.getLogger(__name__)


class ReportService:
    def generate_model_report(
        self,
        db: Session,
        user_id: UUID,
        model_version_id: UUID,
        include_confusion_matrix: bool = True,
        include_roc_curve: bool = True,
        include_feature_importance: bool = True,
    ) -> Report:
        start_time = time.time()

        try:
            model_version = (
                db.query(ModelVersion)
                .filter(ModelVersion.id == model_version_id)
                .first()
            )

            if not model_version:
                raise ValueError(f"Model version {model_version_id} not found")

            metrics = model_version.metrics or {}
            report_id = uuid4()

            total_customers = (
                db.query(CustomerRecord)
                .filter(CustomerRecord.dataset_id == model_version.dataset_id)
                .count()
            )
            churned_customers = (
                db.query(CustomerRecord)
                .filter(
                    CustomerRecord.dataset_id == model_version.dataset_id,
                    CustomerRecord.churn.is_(True),
                )
                .count()
            )
            churn_rate = (churned_customers / total_customers * 100) if total_customers > 0 else 0

            roc_curve_data = None
            if include_roc_curve:
                try:
                    roc_curve_data = ModelEvaluationService.compute_roc_curve(
                        db=db, version_id=model_version_id, user_id=None
                    )
                except Exception as exc:
                    logger.warning(
                        "Skipping ROC curve in report for model %s: %s",
                        model_version_id,
                        exc,
                    )

            feature_importance = None
            if include_feature_importance:
                feature_importance = self._extract_feature_importance(model_version)

            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            story = []
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#1f2937"),
                spaceAfter=30,
                alignment=TA_CENTER,
            )

            heading_style = ParagraphStyle(
                "CustomHeading",
                parent=styles["Heading2"],
                fontSize=16,
                textColor=colors.HexColor("#374151"),
                spaceAfter=12,
            )

            story.append(Paragraph("Customer Churn Prediction Report", title_style))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph("Executive Summary", heading_style))

            summary_data = [
                ["Metric", "Value"],
                ["Report Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
                ["Model Type", model_version.model_type],
                ["Model Version", str(model_version.version)],
                ["Dataset ID", str(model_version.dataset_id)],
                ["Total Customers", f"{total_customers:,}"],
                ["Churn Rate", f"{churn_rate:.2f}%"],
                ["Model Accuracy", self._format_metric(metrics.get("accuracy"))],
                ["Model F1-Score", self._format_metric(metrics.get("f1_score"))],
                [
                    "Training Date",
                    model_version.trained_at.strftime("%Y-%m-%d")
                    if model_version.trained_at
                    else "N/A",
                ],
            ]

            summary_table = Table(summary_data, colWidths=[2.5 * inch, 3 * inch])
            summary_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3b82f6")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            story.append(summary_table)
            story.append(Spacer(1, 0.3 * inch))
            story.append(Paragraph("Model Performance Metrics", heading_style))

            metrics_data = [
                ["Metric", "Value"],
                ["Accuracy", self._format_metric(metrics.get("accuracy"))],
                ["Precision", self._format_metric(metrics.get("precision"))],
                ["Recall", self._format_metric(metrics.get("recall"))],
                ["F1-Score", self._format_metric(metrics.get("f1_score"))],
                ["ROC-AUC", self._format_metric(metrics.get("roc_auc"))],
                ["Training Time", f"{model_version.training_time_seconds:.2f}s"],
            ]

            metrics_table = Table(metrics_data, colWidths=[2.5 * inch, 3 * inch])
            metrics_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10b981")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            story.append(metrics_table)
            story.append(Spacer(1, 0.3 * inch))

            if include_confusion_matrix and model_version.confusion_matrix:
                story.append(PageBreak())
                story.append(Paragraph("Confusion Matrix", heading_style))

                cm_image = self._generate_confusion_matrix_image(model_version.confusion_matrix)
                if cm_image:
                    story.append(Image(cm_image, width=4 * inch, height=4 * inch))
                    story.append(Spacer(1, 0.2 * inch))

            if include_roc_curve and roc_curve_data:
                story.append(PageBreak())
                story.append(Paragraph("ROC Curve", heading_style))

                roc_image = self._generate_roc_curve_image(
                    roc_curve_data, float(metrics.get("roc_auc", 0.0))
                )
                if roc_image:
                    story.append(Image(roc_image, width=5 * inch, height=4 * inch))
                    story.append(Spacer(1, 0.2 * inch))

            if include_feature_importance and feature_importance:
                story.append(PageBreak())
                story.append(Paragraph("Feature Importance", heading_style))

                fi_image = self._generate_feature_importance_image(feature_importance)
                if fi_image:
                    story.append(Image(fi_image, width=5 * inch, height=4 * inch))
                    story.append(Spacer(1, 0.2 * inch))

            doc.build(story)

            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()

            elapsed_time = time.time() - start_time
            if elapsed_time > 10.0:
                logger.warning(
                    "Report generation took %.2fs, exceeding 10-second target",
                    elapsed_time,
                )

            filename = f"model_report_{model_version.model_type}_{report_id}.pdf"
            s3_key = storage_client.upload_report(
                user_id=user_id, report_id=report_id, file_data=pdf_bytes, filename=filename
            )

            report = Report(
                id=report_id,
                user_id=user_id,
                model_version_id=model_version_id,
                report_type="model_evaluation",
                file_path=s3_key,
                report_metadata={
                    "file_size": len(pdf_bytes),
                    "filename": filename,
                    "model_type": model_version.model_type,
                    "version": model_version.version,
                },
                generated_at=datetime.utcnow(),
            )

            db.add(report)
            db.commit()
            db.refresh(report)

            logger.info(
                "Generated report %s for model %s in %.2fs, size=%s bytes",
                report_id,
                model_version_id,
                elapsed_time,
                len(pdf_bytes),
            )

            return report

        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate report: {e}")

    @staticmethod
    def _format_metric(value: Optional[float]) -> str:
        if value is None:
            return "N/A"
        return f"{float(value):.4f}"

    def _extract_feature_importance(self, model_version: ModelVersion) -> Optional[dict[str, float]]:
        try:
            model = MLTrainingService.load_model_from_storage(model_version)
            importances = getattr(model, "feature_importances_", None)
            feature_names = (
                model_version.preprocessing_config.feature_columns
                if model_version.preprocessing_config
                else None
            )

            if importances is None or not feature_names:
                return None

            if len(importances) != len(feature_names):
                logger.warning(
                    "Feature importance length mismatch for model %s: %s != %s",
                    model_version.id,
                    len(importances),
                    len(feature_names),
                )
                return None

            return {
                str(feature_names[index]): float(importances[index])
                for index in range(len(feature_names))
            }
        except Exception as exc:
            logger.warning(
                "Skipping feature importance in report for model %s: %s",
                model_version.id,
                exc,
            )
            return None

    def _generate_confusion_matrix_image(self, confusion_matrix: Any) -> Optional[io.BytesIO]:
        try:
            if isinstance(confusion_matrix, dict):
                cm = np.array(
                    [
                        [
                            confusion_matrix.get("true_negative", 0),
                            confusion_matrix.get("false_positive", 0),
                        ],
                        [
                            confusion_matrix.get("false_negative", 0),
                            confusion_matrix.get("true_positive", 0),
                        ],
                    ]
                )
            else:
                cm = np.array(confusion_matrix, dtype=int)

            if cm.shape != (2, 2):
                logger.warning("Unexpected confusion matrix shape: %s", cm.shape)
                return None

            fig, ax = plt.subplots(figsize=(6, 6))
            im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
            ax.figure.colorbar(im, ax=ax)

            ax.set(
                xticks=np.arange(cm.shape[1]),
                yticks=np.arange(cm.shape[0]),
                xticklabels=["No Churn", "Churn"],
                yticklabels=["No Churn", "Churn"],
                title="Confusion Matrix",
                ylabel="True label",
                xlabel="Predicted label",
            )

            thresh = cm.max() / 2.0 if cm.size else 0
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    ax.text(
                        j,
                        i,
                        format(int(cm[i, j]), "d"),
                        ha="center",
                        va="center",
                        color="white" if cm[i, j] > thresh else "black",
                    )

            fig.tight_layout()

            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
            img_buffer.seek(0)
            plt.close(fig)

            return img_buffer

        except Exception as e:
            logger.error(f"Error generating confusion matrix image: {e}")
            return None

    def _generate_roc_curve_image(
        self, roc_curve_data: dict[str, Any], roc_auc: float
    ) -> Optional[io.BytesIO]:
        try:
            if "points" in roc_curve_data:
                points = roc_curve_data.get("points", [])
                fpr = [point.get("fpr", 0.0) for point in points]
                tpr = [point.get("tpr", 0.0) for point in points]
            else:
                fpr = roc_curve_data.get("fpr", [])
                tpr = roc_curve_data.get("tpr", [])

            if not fpr or not tpr:
                return None

            fig, ax = plt.subplots(figsize=(7, 6))
            ax.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {roc_auc:.4f})")
            ax.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--", label="Random classifier")
            ax.set_xlim([0.0, 1.0])
            ax.set_ylim([0.0, 1.05])
            ax.set_xlabel("False Positive Rate")
            ax.set_ylabel("True Positive Rate")
            ax.set_title("Receiver Operating Characteristic (ROC) Curve")
            ax.legend(loc="lower right")
            ax.grid(True, alpha=0.3)

            fig.tight_layout()

            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
            img_buffer.seek(0)
            plt.close(fig)

            return img_buffer

        except Exception as e:
            logger.error(f"Error generating ROC curve image: {e}")
            return None

    def _generate_feature_importance_image(
        self, feature_importance: dict[str, float]
    ) -> Optional[io.BytesIO]:
        try:
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[
                :15
            ]

            if not sorted_features:
                return None

            features, importances = zip(*sorted_features)

            fig, ax = plt.subplots(figsize=(8, 6))
            y_pos = np.arange(len(features))
            ax.barh(y_pos, importances, align="center", color="steelblue")
            ax.set_yticks(y_pos)
            ax.set_yticklabels(features)
            ax.invert_yaxis()
            ax.set_xlabel("Importance Score")
            ax.set_title("Top 15 Feature Importance")
            ax.grid(True, alpha=0.3, axis="x")

            fig.tight_layout()

            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
            img_buffer.seek(0)
            plt.close(fig)

            return img_buffer

        except Exception as e:
            logger.error(f"Error generating feature importance image: {e}")
            return None
