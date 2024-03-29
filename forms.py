from wtforms import DateTimeField, DecimalField, EmailField, HiddenField, PasswordField, RadioField, StringField, SubmitField
from wtforms.validators import AnyOf, Email, InputRequired, Length, NumberRange, Regexp
from flask_wtf import FlaskForm


'''
INCOMPLETE
'''
class CContract(FlaskForm):
    bounty = DecimalField('bounty', places=2, validators=[InputRequired(), NumberRange(min=10.00, max=10000.00, message="min/max for the bounty")])
    egbonus = DecimalField('egbonus', places=2, validators=[InputRequired(), NumberRange(min=0, max=10000.00, message="min/max for the egbonus")])
    efbonus = DecimalField('efbonus', places=2, validators=[InputRequired(), NumberRange(min=0, max=10000.00, message="min/max for the efbonus")])
    #lostudy = RadioField('lostudy', choices=['high school', 'undergraduate', 'graduate'], validators=[InputRequired()])
    sample = StringField('sample', validators=[InputRequired()])
    specialization = StringField('specialization', validators=[InputRequired()])
    subject = StringField('subject', validators=[InputRequired()])
    submit = StringField('submit')
    #
    aendtime = DateTimeField('aendtime', validators=[])
    ratingtime = DateTimeField('ratingtime', validators=[])
    stalltime = DateTimeField('stalltime', validators=[])
    starttime = DateTimeField('starttime', validators=[])
    tstarttime = DateTimeField('tstarttime', validators=[])
    tendtime = DateTimeField('tendtime', validators=[])


'''
INCOMPLETE
'''
class LoginForm(FlaskForm):
    email = EmailField('email', validators=[InputRequired("email...")])
    password = PasswordField('password', validators=[InputRequired(), Length(min=12, max=50)])


'''
INCOMPLETE
'''
class RegistrationForm(FlaskForm):
    email = StringField('email')
    password = StringField('password')
