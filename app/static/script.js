const punchTypes = [
    "Straight Left",
    "Straight Right",
    "Hook Left",
    "Hook Right",
    "Uppercut"
  ];
  
  let player1 = {
    name: "Player 1",
    punches: {
      "Straight Left": 0,
      "Straight Right": 0,
      "Hook Left": 0,
      "Hook Right": 0,
      "Uppercut": 0
    },
    total: 0,
    hits: 0
  };
  
  let player2 = JSON.parse(JSON.stringify(player1));
  player2.name = "Player 2";
  
  // 🚫 Removed fake data simulation here
  
  // ✅ Real-time Socket.IO Connection
  const socket = io('http://localhost:5000');
  
  socket.emit('get_updates');
  
  // ✅ Handle punch data from backend
  socket.on('punch_data', (data) => {
    const punch = data.punch_type;
    const playerId = data.fighter_id % 2 === 0 ? 2 : 1; 
    const player = playerId === 1 ? player1 : player2;
  
    // Update stats
    player.punches[punch]++;
    player.total++;
    if (data.hit_landed !== false) player.hits++; 
  
    // Update UI
    updateStats(player1, "1");
    updateStats(player2, "2");
    updateLastPunch(punch);
    updateLineChart();
    updateBarChart();
  });
  
  // ✅ Update UI Stats
  function updateStats(player, id) {
    document.getElementById(`totalPunches${id}`).textContent = player.total;
    document.getElementById(`accuracy${id}`).textContent = `${(
      (player.hits / player.total) * 100 || 0
    ).toFixed(1)}%`;
  }
  
  // ✅ Show last punch type
  function updateLastPunch(punch) {
    document.getElementById("lastPunch").textContent = punch;
  }
  
  // ✅ Chart Setup
  const lineCtx = document.getElementById("lineChart").getContext("2d");
  const barCtx = document.getElementById("barChart").getContext("2d");
  
  const lineChart = new Chart(lineCtx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Player 1",
          data: [],
          borderColor: "#ff6384",
          fill: false
        },
        {
          label: "Player 2",
          data: [],
          borderColor: "#36a2eb",
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      animation: false
    }
  });
  
  const barChart = new Chart(barCtx, {
    type: "bar",
    data: {
      labels: punchTypes,
      datasets: [
        {
          label: "Player 1",
          data: [],
          backgroundColor: "#ff6384"
        },
        {
          label: "Player 2",
          data: [],
          backgroundColor: "#36a2eb"
        }
      ]
    },
    options: {
      responsive: true,
      animation: false,
      scales: {
        y: {
          beginAtZero: true
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
  
    // Limit to last 10 points
    if (lineChart.data.labels.length > 10) {
      lineChart.data.labels.shift();
      lineChart.data.datasets[0].data.shift();
      lineChart.data.datasets[1].data.shift();
    }
  
    lineChart.update();
  }
  
  function updateBarChart() {
    barChart.data.datasets[0].data = punchTypes.map(
      (type) => player1.punches[type]
    );
    barChart.data.datasets[1].data = punchTypes.map(
      (type) => player2.punches[type]
    );
    barChart.update();
  }
  