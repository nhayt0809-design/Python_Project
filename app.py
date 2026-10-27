import os
from decimal import Decimal, InvalidOperation
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, abort
)

from config.database import get_connection


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "development-only-key")


# -------------------------
# Dashboard
# -------------------------
@app.route("/")
def index():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            # Get students
            cursor.execute("""
                SELECT s.*, c.course_code, c.course_name
                FROM students s
                JOIN classes c ON s.class_id = c.id
                ORDER BY s.id DESC
            """)
            students = cursor.fetchall()

            # Get classes for the Add Student dropdown
            cursor.execute("""
                SELECT id, course_code, course_name, capacity
                FROM classes
                WHERE status = 'Active'
                ORDER BY id DESC
            """)
            classes = cursor.fetchall()

        return render_template(
            "pages/students.html",
            students=students,
            classes=classes
        )

    finally:
        connection.close()


# -------------------------
# Student list
# -------------------------
@app.route("/students")
def students_page():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s.*, c.course_code, c.course_name
                FROM students s
                JOIN classes c ON s.class_id = c.id
                ORDER BY s.id DESC
            """)
            students = cursor.fetchall()

            cursor.execute("""
                SELECT id, course_code, course_name, capacity
                FROM classes
                WHERE status = 'Active'
                ORDER BY id DESC
            """)
            classes = cursor.fetchall()

        return render_template(
            "pages/students.html",
            students=students,
            classes=classes
        )

    finally:
        connection.close()


# -------------------------
# Register student
# -------------------------
@app.route("/students/create", methods=["POST"])
def create_student():
    student = request.form.get("student", "").strip()
    email = request.form.get("email", "").strip()
    gender = request.form.get("gender", "")
    status = request.form.get("status", "Active")
    class_id = request.form.get("class_id", type=int)

    if not student or not email or gender not in (
        "Male", "Female", "Other"
    ):
        flash("Please complete all student fields.", "error")
        return redirect(url_for("index"))

    if status not in ("Active", "Inactive") or not class_id:
        flash("Please select a valid class and status.", "error")
        return redirect(url_for("index"))

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM classes WHERE id = %s",
                (class_id,)
            )

            if cursor.fetchone() is None:
                flash("The selected class does not exist.", "error")
                return redirect(url_for("index"))

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM students
                WHERE class_id = %s
            """, (class_id,))

            count = cursor.fetchone()["total"]

            cursor.execute("""
                SELECT capacity
                FROM classes
                WHERE id = %s
            """, (class_id,))

            class_info = cursor.fetchone()

            if count >= class_info["capacity"]:
                flash("This class has reached its capacity.", "error")
                return redirect(url_for("index"))

            cursor.execute("""
                INSERT INTO students
                    (student, email, gender, status, class_id,
                    attendance, attendance_count, classwork, `final`, total)
                VALUES (%s, %s, %s, %s, %s, 40, 0, 0, 0, 40)
            """, (student, email, gender, status, class_id))

        connection.commit()
        flash("Student registered successfully!", "success")

    except Exception:
        connection.rollback()
        app.logger.exception("Student registration failed")
        flash("Could not register student. Check the email and database.", "error")

    finally:
        connection.close()

    return redirect(url_for("index"))

# -------------------------
# Update student information
# -------------------------
@app.route("/students/<int:student_id>/update",
           methods=["GET", "POST"])
def update_student(student_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            if request.method == "GET":
                cursor.execute(
                    "SELECT * FROM students WHERE id = %s",
                    (student_id,)
                )
                student = cursor.fetchone()

                if student is None:
                    abort(404)

                return render_template(
                    "pages/edit_student.html",
                    student=student
                )

            student_name = request.form.get("student", "").strip()
            email = request.form.get("email", "").strip()
            gender = request.form.get("gender", "")
            status = request.form.get("status", "")

            cursor.execute("""
                UPDATE students
                SET student = %s,
                    email = %s,
                    gender = %s,
                    status = %s
                WHERE id = %s
            """, (
                student_name,
                email,
                gender,
                status,
                student_id
            ))

        connection.commit()
        flash("Student updated successfully!", "success")

    except Exception:
        connection.rollback()
        app.logger.exception("Student update failed")
        flash("Could not update student. Check the Flask terminal.", "error")

    finally:
        connection.close()

    return redirect(url_for("students_page"))
    # if (
    #     not student
    #     or not email
    #     or gender not in ("Male", "Female", "Other")
    #     or status not in ("Active", "Inactive")
    # ):
    #     flash("Please enter valid student information.", "error")
    #     return redirect(url_for("index"))

    # connection = get_connection()

    # try:
    #     with connection.cursor() as cursor:
    #         cursor.execute("""
    #             UPDATE students
    #             SET student = %s,
    #                 email = %s,
    #                 gender = %s,
    #                 status = %s
    #             WHERE id = %s
    #         """, (student, email, gender, status, student_id))

    #         if cursor.rowcount == 0:
    #             cursor.execute(
    #                 "SELECT id FROM students WHERE id = %s",
    #                 (student_id,)
    #             )
    #             if cursor.fetchone() is None:
    #                 abort(404)

    #     connection.commit()
    #     flash("Student updated successfully!", "success")

    # except Exception:
    #     connection.rollback()
    #     app.logger.exception("Student update failed")
    #     flash("Could not update student. Check the email address.", "error")

    # finally:
    #     connection.close()

    # return redirect(url_for("index"))

# -------------------------
# Update student grades
# -------------------------
@app.route("/students/<int:student_id>/grades", methods=["POST"])
def update_grades(student_id):
    data = request.get_json(silent=True) or {}

    try:
        classwork = Decimal(str(data.get("classwork", "")))
        final_score = Decimal(str(data.get("final", "")))

        if any(
            not value.is_finite() or value < 0 or value > 100
            for value in (classwork, final_score)
        ):
            raise ValueError("Invalid grade")

    except (ValueError, InvalidOperation):
        return jsonify({
            "error": "Enter valid grades between 0 and 100."
        }), 400

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT attendance
                FROM students
                WHERE id = %s
            """, (student_id,))

            row = cursor.fetchone()

            if row is None:
                return jsonify({"error": "Student not found."}), 404

            attendance_score = Decimal(str(row["attendance"] or 0))
            total = attendance_score + classwork + final_score

            cursor.execute("""
                UPDATE students
                SET classwork = %s,
                    `final` = %s,
                    total = %s
                WHERE id = %s
            """, (classwork, final_score, total, student_id))

        connection.commit()

        return jsonify({
            "attendance": float(attendance_score),
            "classwork": float(classwork),
            "final": float(final_score),
            "total": float(total)
        })

    except Exception:
        connection.rollback()
        app.logger.exception("Grade update failed")
        return jsonify({"error": "Could not save grades."}), 500

    finally:
        connection.close()
# -------------------------
# Delete student
# -------------------------
@app.route("/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM students WHERE id = %s",
                (student_id,)
            )

            # Check if student exists
            if cursor.rowcount == 0:
                connection.rollback()
                abort(404)

        # Save changes to database
        connection.commit()

        flash("Student deleted successfully!", "success")

    except Exception:
        connection.rollback()
        app.logger.exception("Student deletion failed")
        flash("Could not delete student.", "error")

    finally:
        connection.close()

    return redirect(url_for("students_page"))


# -------------------------
# Create class
# -------------------------
@app.route("/classes/create", methods=["GET", "POST"])
def create_class():
    if request.method == "GET":
        return render_template("pages/index.html")

    course_name = request.form.get("course_name", "").strip()
    course_code = request.form.get("course_code", "").strip()
    room = request.form.get("room", "").strip()
    capacity = request.form.get("capacity", type=int)
    schedule_days = request.form.get("schedule_days", "")
    status = request.form.get("status", "Active")
    start_time = request.form.get("start_time", "")
    end_time = request.form.get("end_time", "")
    description = request.form.get("description", "").strip()

    if (
        not course_name or not course_code or not room
        or not capacity or capacity < 1
        or not schedule_days or not start_time or not end_time
        or status not in ("Active", "Inactive")
    ):
        flash("Please fill in all required class fields.", "error")
        return redirect(url_for("create_class"))

    try:
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")

        if end <= start:
            flash("End time must be later than start time.", "error")
            return redirect(url_for("create_class"))

    except ValueError:
        flash("Please select valid class times.", "error")
        return redirect(url_for("create_class"))

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO classes
                (course_name, course_code, room, capacity,
                 schedule_days, status, start_time, end_time, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                course_name, course_code, room, capacity,
                schedule_days, status, start_time, end_time, description
            ))

        connection.commit()
        flash("Class created successfully!", "success")

    except Exception:
        connection.rollback()
        app.logger.exception("Class creation failed")
        flash("Could not create class. The course code may already exist.", "error")

    finally:
        connection.close()

    return redirect(url_for("classes_page"))


# -------------------------
# List all classes
# -------------------------
@app.route("/classes")
def classes_page():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    c.*,
                    TIME_FORMAT(c.start_time, '%h:%i %p') AS start_display,
                    TIME_FORMAT(c.end_time, '%h:%i %p') AS end_display,
                    COUNT(s.id) AS student_count
                FROM classes c
                LEFT JOIN students s ON s.class_id = c.id
                GROUP BY c.id
                ORDER BY c.id DESC
            """)
            classes = cursor.fetchall()

        total_capacity = sum(c["capacity"] for c in classes)
        active_count = sum(c["status"] == "Active" for c in classes)
        room_count = len({
            c["room"].strip().lower() for c in classes
        })

        return render_template(
            "pages/classes.html",
            classes=classes,
            total_capacity=total_capacity,
            active_count=active_count,
            room_count=room_count
        )
    finally:
        connection.close()


# -------------------------
# View students in a class
# -------------------------
@app.route("/classes/<int:class_id>/eachstudent")
def eachclass(class_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT *,
                    TIME_FORMAT(start_time, '%%h:%%i %%p') AS start_display,
                    TIME_FORMAT(end_time, '%%h:%%i %%p') AS end_display
                FROM classes
                WHERE id = %s
            """, (class_id,))

            class_info = cursor.fetchone()

            if class_info is None:
                abort(404)

            cursor.execute("""
                SELECT *
                FROM students
                WHERE class_id = %s
                ORDER BY id DESC
            """, (class_id,))

            students = cursor.fetchall()

        return render_template(
            "pages/eachclass.html",
            class_info=class_info,
            students=students
        )

    finally:
        connection.close()


# -------------------------
# Attendance
# -------------------------
@app.route("/students/<int:student_id>/attendance", methods=["POST"])
def mark_attendance(student_id):
    data = request.get_json(silent=True) or {}
    action = data.get("action")

    if action not in ("present", "absent"):
        return jsonify({"error": "Choose present or absent."}), 400

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, attendance_count, attendance
                FROM students
                WHERE id = %s
            """, (student_id,))
            student = cursor.fetchone()

            if student is None:
                return jsonify({"error": "Student not found."}), 404

            if action == "present":
                cursor.execute("""
                    UPDATE students
                    SET attendance_count = attendance_count + 1
                    WHERE id = %s
                """, (student_id,))
            else:
                # An absence deducts one attendance point.
                cursor.execute("""
                    UPDATE students
                    SET attendance = GREATEST(attendance - 1, 0)
                    WHERE id = %s
                """, (student_id,))

            cursor.execute("""
                UPDATE students
                SET total = attendance + classwork + `final`
                WHERE id = %s
            """, (student_id,))

            cursor.execute("""
                SELECT attendance_count, attendance, classwork,
                       `final` AS final_score, total
                FROM students
                WHERE id = %s
            """, (student_id,))
            result = cursor.fetchone()

        connection.commit()
        return jsonify(result)

    except Exception:
        connection.rollback()
        app.logger.exception("Attendance update failed")
        return jsonify({"error": "Could not save attendance."}), 500

    finally:
        connection.close()


@app.route("/save_attendance", methods=["POST"])
def save_attendance():
    student_id = request.form.get("student_id", type=int)
    status = request.form.get("status")

    if not student_id or status not in ["present", "absent"]:
        flash("Please select Present or Absent.", "error")
        return redirect(request.referrer or url_for("classes_page"))

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            if status == "present":
                cursor.execute("""
                    UPDATE students
                    SET attendance_count =
                        COALESCE(attendance_count, 0) + 1
                    WHERE id = %s
                """, (student_id,))

            else:
                cursor.execute("""
                    UPDATE students
                    SET attendance = GREATEST(
                        COALESCE(attendance, 40) - 1, 0
                    )
                    WHERE id = %s
                """, (student_id,))

            if cursor.rowcount == 0:
                connection.rollback()
                flash("Student not found.", "error")
                return redirect(
                    request.referrer or url_for("classes_page")
                )

        connection.commit()
        flash("Attendance saved successfully!", "success")

    except Exception as e:
        connection.rollback()
        print("Attendance error:", e)
        flash("Could not save attendance.", "error")

    finally:
        connection.close()

    return redirect(request.referrer or url_for("classes_page"))



if __name__ == "__main__":
    app.run(debug=True)