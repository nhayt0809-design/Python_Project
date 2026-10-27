const classSearch = document.getElementById("classSearch");
const classStatus = document.getElementById("statusFilter");
const classCards = document.querySelectorAll(".class-card");
const classesFooter = document.getElementById("classesFooter");

function filterClasses() {
    const keyword = classSearch.value.toLowerCase().trim();
    const selectedStatus = classStatus.value.toLowerCase();

    let count = 0;

    classCards.forEach(card => {
        const text = card.textContent.toLowerCase();
        const status = card.dataset.status;

        const matchesText = text.includes(keyword);
        const matchesStatus =
            !selectedStatus || status === selectedStatus;

        const visible = matchesText && matchesStatus;

        card.style.display = visible ? "" : "none";

        if (visible) count++;
    });

    classesFooter.textContent = `Showing ${count} class(es)`;
}

classSearch.addEventListener("input", filterClasses);
classStatus.addEventListener("change", filterClasses);