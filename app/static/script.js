// Punch Types
const punchTypes = [
  "Straight Left",
  "Straight Right",
  "Hook Left",
  "Hook Right",
  "Uppercut"
];

// Players
let player1 = createPlayer("Player 1");
let player2 = createPlayer("Player 2");

function createPlayer(name) {
  return {
    name,
    punches: Object.fromEntries(punchTypes.map(p => [p, 0])),
    total: 0,
    hits: 0
  };
}

// ✅ Socket.IO Setup
const socket = io(window.location.origin);

// Ask backend for latest state on load
socket.emit('get_updates');

// 🔁 Listen for punch updates
socket.on('punch_data', (data) => {
  const punch = data.punch_type;
  const id = data.fighter_id % 2 === 0 ? 2 : 1;
  const player = id === 1 ? player1 : player2;

  if (player.punches[punch] !== undefined) {
    player.punches[punch]++;
    player.total++;
    if (data.hit_landed) player.hits++;

    updateStats(player1, "1");
    updateStats(player2, "2");
    updateLastPunch(punch);
    updateLineChart();
    updateBarChart();
  }
});

// ✅ Update Stats in UI
function updateStats(player, id) {
  document.getElementById(`totalPunches${id}`).textContent = player.total;
  document.getElementById(`accuracy${id}`).textContent = player.total
    ? `${((player.hits / player.total) * 100).toFixed(1)}%`
    : "0%";
}

// ✅ Last Punch Display
function updateLastPunch(punch) {
  document.getElementById("lastPunch").textContent = punch;
}

// ✅ Charts Setup
const lineChart = new Chart(document.getElementById("lineChart").getContext("2d"), {
  type: "line",
  data: {
    labels: [],
    datasets: [
      { label: "Player 1", data: [], borderColor: "#ff6384", fill: false },
      { label: "Player 2", data: [], borderColor: "#36a2eb", fill: false }
    ]
  },
  options: {
    responsive: true,
    animation: false,
    scales: {
      y: {
        beginAtZero: true,
        ticks: { stepSize: 1 }
      }
    }
  }
});

const barChart = new Chart(document.getElementById("barChart").getContext("2d"), {
  type: "bar",
  data: {
    labels: punchTypes,
    datasets: [
      { label: "Player 1", data: [], backgroundColor: "#ff6384" },
      { label: "Player 2", data: [], backgroundColor: "#36a2eb" }
    ]
  },
  options: {
    responsive: true,
    animation: false,
    scales: {
      y: {
        beginAtZero: true,
        ticks: { stepSize: 1 }
      }
    }
  }
});

// ✅ Update Chart Data
function updateLineChart() {
  const time = new Date().toLocaleTimeString();
  lineChart.data.labels.push(time);
  lineChart.data.datasets[0].data.push(player1.total);
  lineChart.data.datasets[1].data.push(player2.total);

  // Limit to last 10 entries
  if (lineChart.data.labels.length > 10) {
    lineChart.data.labels.shift();
    lineChart.data.datasets[0].data.shift();
    lineChart.data.datasets[1].data.shift();
  }

  lineChart.update();
}

function updateBarChart() {
  barChart.data.datasets[0].data = punchTypes.map(p => player1.punches[p]);
  barChart.data.datasets[1].data = punchTypes.map(p => player2.punches[p]);
  barChart.update();
}
