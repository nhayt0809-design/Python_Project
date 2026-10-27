const studentModal = document.getElementById("studentModal");

function openStudentForm() {
    studentModal.classList.add("show");
}

function closeStudentForm() {
    studentModal.classList.remove("show");
}

studentModal.addEventListener("click", function (event) {
    if (event.target === studentModal) {
        closeStudentForm();
    }
});

document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
        closeStudentForm();
    }
});

const searchInput = document.getElementById("searchInput");
const statusFilter = document.getElementById("statusFilter");
const visibleCount = document.getElementById("visibleCount");

function searchStudents() {
    const keyword = searchInput.value.toLowerCase().trim();
    const selectedStatus = statusFilter.value.toLowerCase();

    const rows = document.querySelectorAll("#studentTable .student-row");
    let count = 0;

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const status = row.dataset.status;

        const matchesSearch = text.includes(keyword);
        const matchesStatus =
            !selectedStatus || status === selectedStatus;

        const visible = matchesSearch && matchesStatus;

        row.style.display = visible ? "" : "none";

        if (visible) count++;
    });

    visibleCount.textContent = count;
}

searchInput.addEventListener("input", searchStudents);
statusFilter.addEventListener("change", searchStudents);