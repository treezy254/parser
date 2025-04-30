function toggleModal() {
  const modal = document.getElementById("configModal");
  modal.style.display = modal.style.display === "flex" ? "none" : "flex";
}

// Charts
const ctx1 = document.getElementById("performanceGraph").getContext("2d");
new Chart(ctx1, {
  type: "line",
  data: {
    labels: ["10K", "250K", "1M"],
    datasets: [
      {
        label: "Execution Time (ms)",
        data: [20, 500, 2000],
        borderColor: "blue",
        fill: false,
      },
    ],
  },
});

const ctx2 = document.getElementById("additionalChart").getContext("2d");
new Chart(ctx2, {
  type: "bar",
  data: {
    labels: [
      "Linear",
      "Hash Set",
      "Binary",
      "Trie",
      "Boyer-Moore",
      "Rabin-Karp",
      "Aho-Corasick",
    ],
    datasets: [
      {
        label: "Performance Score",
        data: [3, 9, 8, 10, 6, 7, 9],
        backgroundColor: "#3498db",
      },
    ],
  },
});

// Debug Logs Stream
setInterval(() => {
  const logStream = document.getElementById("logStream");
  const timestamp = new Date().toLocaleTimeString();
  const newLog = document.createElement("p");
  newLog.textContent = `[DEBUG] Query at ${timestamp} - Result: Found`;
  logStream.appendChild(newLog);
  logStream.scrollTop = logStream.scrollHeight;
}, 2000);
