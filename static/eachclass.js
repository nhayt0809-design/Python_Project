
document.addEventListener("DOMContentLoaded", function () {
    // Find all student rows and their controls
    const studentRows = document.querySelectorAll(".student-row");

    // Show a message to the user
    function showMessage(message, type = "success") {
        let messageBox = document.getElementById("attendanceMessage");

        if (!messageBox) {
            messageBox = document.createElement("div");
            messageBox.id = "attendanceMessage";
            messageBox.className = "attendance-message";

            const pageHeader = document.querySelector(".welcome");

            if (pageHeader) {
                pageHeader.insertAdjacentElement("afterend", messageBox);
            } else {
                document.body.prepend(messageBox);
            }
        }

        messageBox.textContent = message;
        messageBox.dataset.type = type;
        messageBox.style.display = "block";
    }

    // Send data to a Flask route
    async function sendRequest(url, data) {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(data)
        });

        let result;

        try {
            result = await response.json();
        } catch {
            throw new Error(
                "The server did not return JSON. Check your Flask route."
            );
        }

        if (!response.ok) {
            throw new Error(result.message || result.error || "Request failed.");
        }

        if (result.success === false) {
            throw new Error(result.message || result.error || "Unable to save.");
        }

        return result;
    }

    // Update an element's text if it exists
    function updateText(row, selector, value) {
        const element = row.querySelector(selector);

        if (element && value !== undefined && value !== null) {
            element.textContent = value;
        }
    }

    // Find a row's student ID
    function getStudentId(row) {
        return row.dataset.studentId || row.dataset.id;
    }

    // --------------------------------
    // PRESENT / ABSENT BUTTONS
    // --------------------------------

    document.querySelectorAll(".btn-present, .btn-absent").forEach(button => {
        button.addEventListener("click", async function () {
            const row = button.closest(".student-row");

            if (!row) {
                showMessage("Cannot find this student's row.", "error");
                return;
            }

            const studentId = getStudentId(row);
            const action = button.classList.contains("btn-present")
                ? "present"
                : "absent";

            if (!studentId) {
                showMessage("Student ID is missing from the table row.", "error");
                return;
            }

            const buttons = row.querySelectorAll(".btn-present, .btn-absent");

            buttons.forEach(item => {
                item.disabled = true;
            });

            try {
                const result = await sendRequest(
                    `/students/${studentId}/attendance`,
                    { action: action }
                );

                // Update values returned by Flask
                if (result.attendance !== undefined) {
                    updateText(row, ".attendance-score", result.attendance);
                }

                if (result.attendance_count !== undefined) {
                    updateText(
                        row,
                        ".attendance-count",
                        result.attendance_count
                    );
                }

                if (result.total !== undefined) {
                    updateText(row, ".total-score", result.total);
                }

                showMessage(
                    result.message ||
                    (action === "present"
                        ? "Attendance marked present."
                        : "Attendance marked absent.")
                );
            } catch (error) {
                showMessage(error.message, "error");
            } finally {
                buttons.forEach(item => {
                    item.disabled = false;
                });
            }
        });
    });

    // --------------------------------
    // SAVE CLASSWORK AND FINAL GRADES
    // --------------------------------

    document.querySelectorAll(".btn-save-grades").forEach(button => {
        button.addEventListener("click", async function () {
            const row = button.closest(".student-row");

            if (!row) {
                showMessage("Cannot find this student's row.", "error");
                return;
            }

            const studentId = getStudentId(row);

            if (!studentId) {
                showMessage("Student ID is missing from the table row.", "error");
                return;
            }

            const classworkInput = row.querySelector(".classwork-input");
            const finalInput = row.querySelector(".final-input");

            if (!classworkInput || !finalInput) {
                showMessage(
                    "Cannot find the Classwork or Final input field.",
                    "error"
                );
                return;
            }

            const classwork = Number(classworkInput.value);
            const finalGrade = Number(finalInput.value);

            if (
                classworkInput.value.trim() === "" ||
                finalInput.value.trim() === "" ||
                !Number.isFinite(classwork) ||
                !Number.isFinite(finalGrade) ||
                classwork < 0 ||
                finalGrade < 0
            ) {
                showMessage("Enter valid non-negative grade values.", "error");
                return;
            }

            button.disabled = true;
            const originalText = button.textContent;
            button.textContent = "Saving...";

            try {
                const result = await sendRequest(
                    `/students/${studentId}/grades`,
                    {
                        classwork: classwork,
                        final: finalGrade
                    }
                );

                if (result.classwork !== undefined) {
                    updateText(row, ".classwork-score", result.classwork);
                }

                if (result.final !== undefined) {
                    updateText(row, ".final-score", result.final);
                }

                if (result.total !== undefined) {
                    updateText(row, ".total-score", result.total);
                }

                showMessage(result.message || "Grades saved successfully.");
            } catch (error) {
                showMessage(error.message, "error");
            } finally {
                button.disabled = false;
                button.textContent = originalText;
            }
        });
    });

    // --------------------------------
    // OPTIONAL: UPDATE TOTAL ON SCREEN
    // --------------------------------

    studentRows.forEach(row => {
        const classworkInput = row.querySelector(".classwork-input");
        const finalInput = row.querySelector(".final-input");

        if (!classworkInput || !finalInput) {
            return;
        }

        function previewTotal() {
            const attendanceElement = row.querySelector(".attendance-score");
            const attendance = Number(
                attendanceElement?.textContent || 0
            );
            const classwork = Number(classworkInput.value || 0);
            const finalGrade = Number(finalInput.value || 0);

            const totalElement = row.querySelector(".total-score");

            if (totalElement) {
                totalElement.textContent = attendance + classwork + finalGrade;
            }
        }

        classworkInput.addEventListener("input", previewTotal);
        finalInput.addEventListener("input", previewTotal);
    });
});
