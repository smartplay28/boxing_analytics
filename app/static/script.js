// =================================
//  Constants
// =================================
const PUNCH_TYPES = [
  "Straight Left",
  "Straight Right",
  "Hook Left",
  "Hook Right",
  "Uppercut"
];

// =================================
//  Player Objects
// =================================
function createPlayer(name) {
  return {
      name,
      punches: Object.fromEntries(PUNCH_TYPES.map(p => [p, 0])),
      total: 0,
      hits: 0
  };
}

const player1 = createPlayer("Player 1");
const player2 = createPlayer("Player 2");

// =================================
//  Socket.IO Setup
// =================================
const socket = io(window.location.origin);

// Event Handlers
socket.on('connect', () => {
  console.log('Connected to server');
  updateStatusLabel('CONNECTED', 'green');
  socket.emit('get_updates'); // Request initial data
});

socket.on('disconnect', () => {
  console.log('Disconnected from server');
  updateStatusLabel('DISCONNECTED', 'red');
});

socket.on('connect_error', (error) => {
  console.error('Connection Error:', error);
  updateStatusLabel('CONNECTION ERROR', 'red');
});

// =================================
//  UI Updates
// =================================
function updateStatusLabel(text, color) {
  const statusLabel = document.getElementById('statusLabel');
  statusLabel.textContent = text;
  statusLabel.style.backgroundColor = color;
}

function updatePlayerStats(player, playerId) {
  document.getElementById(`totalPunches${playerId}`).textContent = player.total;
  document.getElementById(`accuracy${playerId}`).textContent = player.total
      ? `${((player.hits / player.total) * 100).toFixed(1)}%`
      : "0%";
}

function updateLastPunchDisplay(punch) {
  document.getElementById("lastPunch").textContent = punch;
}

// =================================
//  Chart Updates
// =================================
function updateLineChartData() {
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

function updateBarChartData() {
  barChart.data.datasets[0].data = PUNCH_TYPES.map(p => player1.punches[p]);
  barChart.data.datasets[1].data = PUNCH_TYPES.map(p => player2.punches[p]);
  barChart.update();
}

// =================================
//  Chart Initialization
// =================================
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
      labels: PUNCH_TYPES,
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

// =================================
//  Socket.IO Message Handling
// =================================
socket.on('punch_data', (data) => {
  const punch = data.punch_type;
  const playerId = data.fighter_id % 2 === 0 ? 2 : 1;
  const player = playerId === 1 ? player1 : player2;

  if (player.punches[punch] !== undefined) {
      player.punches[punch]++;
      player.total++;
      if (data.hit_landed) player.hits++;

      updatePlayerStats(player1, "1");
      updatePlayerStats(player2, "2");
      updateLastPunchDisplay(punch);
      updateLineChartData();
      updateBarChartData();
  }
});