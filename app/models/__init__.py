from app.extensions import db

###
#
# ✅ MAJOR # Carrera
#
###
class Major(db.Model):
    __tablename__ = 'majors'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)

    students = db.relationship('Student', backref='major', lazy=True)

    def __str__(self):
        return f"Major: {self.code}"

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
        }

###
#
# ✅ STUDENT
#
###
class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    identification = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)

    major_id = db.Column(db.Integer, db.ForeignKey('majors.id'), nullable=False, index=True)

    grades = db.relationship('Grade', backref='student', lazy=True)

    def __str__(self):
        return f"Student: {self.identification}, Name: {self.full_name}"

    def to_dict(self):
        return {
            'id': self.id,
            'identification': self.identification,
            'full_name': self.full_name,
        }

###
#
# ✅ SUBJECT # Asignatura
#
###
class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)

    def __str__(self):
        return f"Subject: {self.code}, Name: {self.name}"

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

###
#
# ✅ ACADEMIC PERIOD # Periodo Academico
#
###
class AcademicPeriod(db.Model):
    __tablename__ = 'academic_periods'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    uploaded_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
    )
    uploaded_at = db.Column(db.DateTime, nullable=True)
    source_file = db.Column(db.String(255), nullable=True)

    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id])

    def __str__(self):
        return f"Academic Period: {self.code}"

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'uploaded_by_id': self.uploaded_by_id,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'source_file': self.source_file,
        }

###
#
# ✅ GRADE # Nota
#
###
class Grade(db.Model):
    __tablename__ = 'grades'

    id = db.Column(db.Integer, primary_key=True)
    final_score = db.Column(db.String(20), nullable=False)
    condition = db.Column(db.String(20))
    # Explicit absent flag instead of inferring from final_score string
    absent = db.Column(db.Boolean, nullable=False, default=False, server_default='false')

    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False, index=True)
    academic_period_id = db.Column(db.Integer, db.ForeignKey('academic_periods.id'), nullable=True, index=True)

    subject = db.relationship('Subject')
    academic_period = db.relationship('AcademicPeriod')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_id', 'academic_period_id', name='uq_grade_student_subject_period'),
    )

    def __str__(self):
        return f"Grade: {self.final_score}, Condition: {self.condition}"

    def to_dict(self):
        return {
            'id': self.id,
            'final_score': self.final_score,
            'condition': self.condition,
            'absent': self.absent,
            'student_id': self.student_id,
            'subject_id': self.subject_id,
            'academic_period_id': self.academic_period_id,
        }
