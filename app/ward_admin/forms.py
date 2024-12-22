from flask_wtf import FlaskForm
from wtforms import FloatField, SelectField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional, Length


class ApplicationReviewForm(FlaskForm):
    amount_allocated = FloatField(
        "Amount to Allocate", validators=[DataRequired(), NumberRange(min=0)]
    )
    status = SelectField(
        "Status",
        choices=[
            ("PENDING", "Pending"),
            ("APPROVED", "Approve"),
            ("REJECTED", "Reject"),
        ],
        validators=[DataRequired()],
    )
    review_note = TextAreaField(
        "Review Notes", validators=[Optional(), Length(max=500)]
    )
