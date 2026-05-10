import io
import logging
import time
from datetime import datetime
from typing import Dict, Optional
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

from backend.domain.models.model_version import ModelVersion
from backend.domain.models.report import Report
from backend.infrastructure.storage import storage_client

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
                .filter(ModelVersion.id == model_version_id, ModelVersion.user_id == user_id)
                .first()
            )

            if not model_version:
                raise ValueError(f"Model version {model_version_id} not found")

            report_id = uuid4()

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

            from backend.domain.models.customer_record import CustomerRecord

            total_customers = (
                db.query(CustomerRecord).filter(CustomerRecord.user_id == user_id).count()
            )

            churned_customers = (
                db.query(CustomerRecord)
                .filter(CustomerRecord.user_id == user_id, CustomerRecord.churn.is_(True))
                .count()
            )

            churn_rate = (churned_customers / total_customers * 100) if total_customers > 0 else 0

            summary_data = [
                ["Metric", "Value"],
                ["Report Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
                ["Model Type", model_version.model_type],
                ["Model Version", str(model_version.version)],
                ["Total Customers", f"{total_customers:,}"],
                ["Churn Rate", f"{churn_rate:.2f}%"],
                [
                    "Model Accuracy",
                    f"{model_version.accuracy:.4f}" if model_version.accuracy else "N/A",
                ],
                [
                    "Model F1-Score",
                    f"{model_version.f1_score:.4f}" if model_version.f1_score else "N/A",
                ],
                ["Training Date", model_version.created_at.strftime("%Y-%m-%d")],
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
                ["Accuracy", f"{model_version.accuracy:.4f}" if model_version.accuracy else "N/A"],
                [
                    "Precision",
                    f"{model_version.precision:.4f}" if model_version.precision else "N/A",
                ],
                ["Recall", f"{model_version.recall:.4f}" if model_version.recall else "N/A"],
                ["F1-Score", f"{model_version.f1_score:.4f}" if model_version.f1_score else "N/A"],
                ["ROC-AUC", f"{model_version.roc_auc:.4f}" if model_version.roc_auc else "N/A"],
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

            if include_roc_curve and model_version.roc_curve_data:
                story.append(PageBreak())
                story.append(Paragraph("ROC Curve", heading_style))

                roc_image = self._generate_roc_curve_image(
                    model_version.roc_curve_data, model_version.roc_auc
                )
                if roc_image:
                    story.append(Image(roc_image, width=5 * inch, height=4 * inch))
                    story.append(Spacer(1, 0.2 * inch))

            if include_feature_importance and model_version.feature_importance:
                story.append(PageBreak())
                story.append(Paragraph("Feature Importance", heading_style))

                fi_image = self._generate_feature_importance_image(model_version.feature_importance)
                if fi_image:
                    story.append(Image(fi_image, width=5 * inch, height=4 * inch))
                    story.append(Spacer(1, 0.2 * inch))

            doc.build(story)

            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()

            elapsed_time = time.time() - start_time
            if elapsed_time > 10.0:
                logger.warning(
                    f"Report generation took {elapsed_time:.2f}s, " f"exceeding 10-second target"
                )

            filename = f"model_report_{model_version.model_type}_v{model_version.version}.pdf"
            s3_key = storage_client.upload_report(
                user_id=user_id, report_id=report_id, file_data=pdf_bytes, filename=filename
            )

            report = Report(
                id=report_id,
                user_id=user_id,
                model_version_id=model_version_id,
                report_type="model_evaluation",
                file_path=s3_key,
                file_size=len(pdf_bytes),
                created_at=datetime.utcnow(),
            )

            db.add(report)
            db.commit()
            db.refresh(report)

            logger.info(
                f"Generated report {report_id} for model {model_version_id} "
                f"in {elapsed_time:.2f}s, size={len(pdf_bytes)} bytes"
            )

            return report

        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate report: {e}")

    def _generate_confusion_matrix_image(self, confusion_matrix: Dict) -> Optional[io.BytesIO]:
        try:
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

            thresh = cm.max() / 2.0
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    ax.text(
                        j,
                        i,
                        format(cm[i, j], "d"),
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
        self, roc_curve_data: Dict, roc_auc: float
    ) -> Optional[io.BytesIO]:
        try:
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

    def _generate_feature_importance_image(self, feature_importance: Dict) -> Optional[io.BytesIO]:
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
