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
    uploaded_by_email    = db.Column(db.String(100), nullable=True)
    uploaded_by_fullname = db.Column(db.String(200), nullable=True)
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
            'uploaded_by_email': self.uploaded_by_email,
            'uploaded_by_fullname': self.uploaded_by_fullname,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'source_file': self.source_file,
        }

###
#
# ✅ ACADEMIC PERIOD AUDIT # Auditoría de períodos académicos
#
###
class AcademicPeriodAudit(db.Model):
    __tablename__ = 'academic_periods_audit'

    id            = db.Column(db.Integer, primary_key=True)
    period_code   = db.Column(db.String(20), nullable=False)
    operation     = db.Column(db.String(10), nullable=False)
    user_email    = db.Column(db.String(100), nullable=True)
    user_fullname = db.Column(db.String(200), nullable=True)
    operation_at  = db.Column(db.DateTime, nullable=False)
    source_file   = db.Column(db.String(255), nullable=True)
    ip_address    = db.Column(db.String(45), nullable=True)
    affected_rows = db.Column(db.JSON, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'period_code': self.period_code,
            'operation': self.operation,
            'user_email': self.user_email,
            'user_fullname': self.user_fullname,
            'operation_at': self.operation_at.isoformat() if self.operation_at else None,
            'source_file': self.source_file,
            'ip_address': self.ip_address,
            'affected_rows': self.affected_rows,
        }

###
#
# ✅ GRADE # Nota
#
###
class Grade(db.Model):
    __tablename__ = 'grades'

    id        = db.Column(db.Integer, primary_key=True)
    condition = db.Column(db.String(20))          # RG | RP
    absent    = db.Column(db.Boolean, nullable=False, default=False, server_default='false')

    # Objetivos individuales (columnas T1–T6 del archivo .REP)
    obj_1 = db.Column(db.Boolean, nullable=False, default=False, server_default='false')
    obj_2 = db.Column(db.Boolean, nullable=False, default=False, server_default='false')
    obj_3 = db.Column(db.Boolean, nullable=False, default=False, server_default='false')
    obj_4 = db.Column(db.Boolean, nullable=False, default=False, server_default='false')
    obj_5 = db.Column(db.Boolean, nullable=False, default=False, server_default='false')
    obj_6 = db.Column(db.Boolean, nullable=False, default=False, server_default='false')
    objectives_max = db.Column(db.Integer, nullable=False, default=0, server_default='0')

    student_id         = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    subject_id         = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False, index=True)
    academic_period_id = db.Column(db.Integer, db.ForeignKey('academic_periods.id'), nullable=True, index=True)

    subject         = db.relationship('Subject')
    academic_period = db.relationship('AcademicPeriod')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_id', 'academic_period_id', name='uq_grade_student_subject_period'),
    )

    @property
    def objectives_achieved(self) -> int:
        return sum([self.obj_1, self.obj_2, self.obj_3, self.obj_4, self.obj_5, self.obj_6])

    def __str__(self):
        return f"Grade: {self.objectives_achieved}/{self.objectives_max}, Condition: {self.condition}"

    def to_dict(self):
        return {
            'id': self.id,
            'condition': self.condition,
            'absent': self.absent,
            'objectives_achieved': self.objectives_achieved,
            'objectives_max': self.objectives_max,
            'obj_1': self.obj_1,
            'obj_2': self.obj_2,
            'obj_3': self.obj_3,
            'obj_4': self.obj_4,
            'obj_5': self.obj_5,
            'obj_6': self.obj_6,
            'student_id': self.student_id,
            'subject_id': self.subject_id,
            'academic_period_id': self.academic_period_id,
        }
