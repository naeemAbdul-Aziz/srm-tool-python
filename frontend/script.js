// JavaScript for Modern, Interactive Student Management Frontend
const API_BASE_URL = "http://localhost:8000";

function createStudentRow(student) {
  const tr = document.createElement('tr');
  ['index_number', 'full_name', 'course', 'score', 'grade'].forEach(key => {
    const td = document.createElement('td');
    td.textContent = student[key] ?? '';
    tr.appendChild(td);
  });
  return tr;
}

async function loadAllStudents() {
  const tbody = document.querySelector('#students-table tbody');
  tbody.innerHTML = '<tr><td colspan="5">Loading...</td></tr>';

  try {
    const res = await fetch(`${API_BASE_URL}/students`);
    const students = await res.json();

    tbody.innerHTML = '';
    if (students.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5">No students found.</td></tr>';
      return;
    }

    students.forEach(student => tbody.appendChild(createStudentRow(student)));
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="error">${err.message}</td></tr>`;
  }
}

async function searchStudent() {
  const index = document.getElementById('search-index').value.trim();
  const resultDiv = document.getElementById('search-result');
  resultDiv.innerHTML = '';

  if (!index) {
    resultDiv.textContent = 'Please enter an index number.';
    resultDiv.className = 'error';
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/students/${index}`);
    if (res.status === 404) throw new Error('Student not found.');

    const student = await res.json();
    resultDiv.innerHTML = `
      <div class="card">
        <h3>${student.full_name}</h3>
        <p><strong>Index:</strong> ${student.index_number}</p>
        <p><strong>Course:</strong> ${student.course}</p>
        <p><strong>Score:</strong> ${student.score}</p>
        <p><strong>Grade:</strong> ${student.grade}</p>
      </div>
    `;
    resultDiv.className = 'success';
  } catch (err) {
    resultDiv.textContent = err.message;
    resultDiv.className = 'error';
  }
}

async function addStudent(event) {
  event.preventDefault();
  const index = document.getElementById('add-index').value.trim();
  const name = document.getElementById('add-name').value.trim();
  const course = document.getElementById('add-course').value.trim();
  const score = Number(document.getElementById('add-score').value);
  const msgDiv = document.getElementById('add-student-message');
  msgDiv.textContent = '';

  if (!index || !name || !course || isNaN(score) || score < 0 || score > 100) {
    msgDiv.textContent = 'Fill all fields correctly.';
    msgDiv.className = 'error';
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/students`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ index_number: index, full_name: name, course, score })
    });

    const data = await res.json();
    msgDiv.textContent = data.message;
    msgDiv.className = 'success';
    document.getElementById('add-student-form').reset();
    loadAllStudents();
  } catch (err) {
    msgDiv.textContent = err.message;
    msgDiv.className = 'error';
  }
}

async function updateScore(event) {
  event.preventDefault();
  const index = document.getElementById('update-index').value.trim();
  const score = Number(document.getElementById('update-score').value);
  const msgDiv = document.getElementById('update-score-message');

  if (!index || isNaN(score) || score < 0 || score > 100) {
    msgDiv.textContent = 'Invalid input.';
    msgDiv.className = 'error';
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/students/${index}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ score })
    });

    const data = await res.json();
    msgDiv.textContent = data.message;
    msgDiv.className = 'success';
    document.getElementById('update-score-form').reset();
    loadAllStudents();
  } catch (err) {
    msgDiv.textContent = err.message;
    msgDiv.className = 'error';
  }
}

async function uploadFile(event) {
  event.preventDefault();
  const fileInput = document.getElementById('upload-file');
  const msgDiv = document.getElementById('upload-file-message');

  if (!fileInput.files.length) {
    msgDiv.textContent = 'Select a file to upload.';
    msgDiv.className = 'error';
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch(`${API_BASE_URL}/students/upload`, {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    msgDiv.textContent = data.message;
    msgDiv.className = 'success';
    fileInput.value = '';
    loadAllStudents();
  } catch (err) {
    msgDiv.textContent = err.message;
    msgDiv.className = 'error';
  }
}

document.getElementById('refresh-students-btn').addEventListener('click', loadAllStudents);
document.getElementById('search-btn').addEventListener('click', searchStudent);
document.getElementById('add-student-form').addEventListener('submit', addStudent);
document.getElementById('update-score-form').addEventListener('submit', updateScore);
document.getElementById('upload-file-form').addEventListener('submit', uploadFile);

loadAllStudents();
