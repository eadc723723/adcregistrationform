document.addEventListener("DOMContentLoaded", function () {
  function filterStudents() {
    const idNoFilter = document.getElementById("idNoFilter").value.toLowerCase();
    const nameFilter = document.getElementById("nameFilter").value.toLowerCase();
    const agentCodeFilter = document.getElementById("agentCodeFilter").value.toLowerCase();
    const dateFromFilter = document.getElementById("dateFromFilter").value;
    const dateToFilter = document.getElementById("dateToFilter").value;

    if (!idNoFilter && !nameFilter && !agentCodeFilter && !dateFromFilter && !dateToFilter) {
      alert("Please enter at least one filter criteria.");
      return;
    }

    fetch(`/filter-students/?id_no=${idNoFilter}&name=${nameFilter}&agent_code=${agentCodeFilter}&date_from=${dateFromFilter}&date_to=${dateToFilter}`)
      .then((response) => response.json())
      .then((data) => {
        const tbody = document.querySelector("#studentsTable tbody");
        tbody.innerHTML = "";

        if (data.students.length === 0) {
          tbody.innerHTML = "<tr><td colspan='8' class='text-center'>No data available</td></tr>";
        } else {
          data.students.forEach((student) => {
            const row = document.createElement("tr");

            row.innerHTML = `
              <td>${student.counter}</td>
              <td>${student.name}</td>
              <td>${student.id_no}</td>
              <td>${student.class_types.join(", ")}</td>
              <td>${student.registration_form}</td>
              <td>${student.agent_code} ${student.agent_name}</td>
              <td>${student.registration_date}</td>
              <td><a href="/student-details/${student.id}" class="btn btn-info">Details</a></td>
            `;

            tbody.appendChild(row);
          });
        }
      });
  }

  function clearFilters() {
    document.getElementById("idNoFilter").value = "";
    document.getElementById("nameFilter").value = "";
    document.getElementById("agentCodeFilter").value = "";
    document.getElementById("dateFromFilter").value = "";
    document.getElementById("dateToFilter").value = "";
    document.querySelector("#studentsTable tbody").innerHTML = "";
  }

  document.getElementById("searchButton").addEventListener("click", filterStudents);
  document.getElementById("clearButton").addEventListener("click", clearFilters);
});
