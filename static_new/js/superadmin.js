
document.getElementById('updateLimitsButton').addEventListener('click', function () {
    // Получаем значения из полей ввода
    const departmentSelect = document.getElementById('departmentSelect');
    const deviceLimit = document.getElementById('deviceLimit').value;
    const photoLimit = document.getElementById('photoLimit').value;

    var selectedDepartment = departmentSelect.value;
    var departmentGuid = departmentSelect.options[selectedDepartment].getAttribute('data-department-guid');

    // Проверка: выбрано ли подразделение
    if (!departmentGuid) {
        alert("Пожалуйста, выберите подразделение.");
        return;
    }

    // Формируем данные для отправки
    const data = {
        hash: hash_admin,
        device_id: device_id,
        department: departmentGuid,
        max_divice_count: parseInt(deviceLimit, 10), // Преобразуем в число
        max_photo_count: parseInt(photoLimit, 10) // Преобразуем в число
    };

    // Отправка данных на сервер
    fetch('/update_department_settings', { // Замените на нужный URL
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка при обновлении лимитов');
        }
        return response.json();
    })
    .then(result => {
        showCenteredBlock('Лимиты успешно обновлены');
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Не удалось обновить лимиты');
    });
});


// Функция для загрузки данных о подразделении при выборе опции
document.getElementById("departmentSelect").addEventListener("change", async function () {
    var selectedDepartment = this.value;
    var departmentGuid = departmentSelect.options[selectedDepartment].getAttribute('data-department-guid');

    // Проверяем, что подразделение выбрано
    if (departmentGuid) {
        try {
            // Отправляем POST-запрос к API для получения данных о подразделении
            const response = await fetch('/get_department_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    hash: hash_admin,
                    department: departmentGuid 
                })
            });
            
            // Проверка на успешный ответ
            if (!response.ok) {
                throw new Error('Ошибка загрузки данных');
            }

            document.getElementById('limit_field').style.display = 'block';

            // Получаем данные в формате JSON
            const data_json = await response.json();
            const data = data_json.department_data;
            console.log(data);

            // Устанавливаем лимиты устройств и фото
            document.getElementById("deviceLimit").value = data.settings.max_divice_count;
            document.getElementById("photoLimit").value = data.settings.max_photo_count;

            // Очищаем таблицу, кроме заголовка
            const tableBody = document.getElementById("deviceList").getElementsByTagName('tbody')[0] ||
                              document.getElementById("deviceList").appendChild(document.createElement('tbody'));
            tableBody.innerHTML = "";

            // Добавляем заголовок таблицы
            if (data.devises.length > 0) {
                const headerRow = document.createElement("tr");
                headerRow.innerHTML = `
                    <th>Номер</th>
                    <th>Логин</th>
                    <th>Имя</th>
                    <th>ИД Устройства</th>
                    <th>Удалить</th>
                `;
                tableBody.appendChild(headerRow);
            }

            // Заполняем таблицу данными об устройствах
            data.devises.forEach((device, index) => {
                const row = document.createElement("tr");

                // Создаем ячейки и добавляем их в строку
                const cellNumber = document.createElement("td");
                cellNumber.textContent = index + 1;

                const cellLogin = document.createElement("td");
                cellLogin.textContent = device.admin.login;
                
                const cellName = document.createElement("td");
                cellName.textContent = device.admin.name;

                const cellDeviceId = document.createElement("td");
                cellDeviceId.textContent = device.id;

                const cellDeleteButton = document.createElement("td");
                const deleteButton = document.createElement("button");
                deleteButton.classList.add("remove-icon", "deleteAdminButton");
                deleteButton.dataset.deviceId = device.id;

                const deleteIcon = document.createElement("img");
                deleteIcon.src = "static/images/trash-red.png";
                deleteButton.appendChild(deleteIcon);

                // Добавляем обработчик для удаления устройства
                deleteButton.addEventListener("click", async function () {
                    try {
                        // Получаем ID устройства для удаления
                        const deviceId = deleteButton.dataset.deviceId;
                        
                        // Выполняем DELETE-запрос к API для удаления устройства
                        const deleteResponse = await fetch(`/delete_device/${deviceId}`, {
                            method: 'DELETE',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${hash_admin}`
                            }
                        });

                        // Проверяем успешность запроса
                        if (!deleteResponse.ok) {
                            throw new Error('Ошибка удаления устройства');
                        }

                        // Удаляем строку из таблицы после успешного ответа API
                        row.remove();
                    } catch (error) {
                        console.error("Ошибка удаления устройства:", error);
                    }
                });

                // Вставляем ячейки в строку
                cellDeleteButton.appendChild(deleteButton);
                row.appendChild(cellNumber);
                row.appendChild(cellLogin);
                row.appendChild(cellName);
                row.appendChild(cellDeviceId);
                row.appendChild(cellDeleteButton);

                // Добавляем строку в таблицу
                tableBody.appendChild(row);
            });
        } catch (error) {
            console.error("Ошибка при загрузке данных о подразделении:", error);
        }
    }
    else {
        document.getElementById('limit_field').style.display = 'none';
    }
});

document.getElementById("fetchLogsButton").addEventListener("click", function() {
    const date = document.getElementById("datePicker").value;

    const requestData = {
        date: date,
        hash: hash_admin
    };

    fetch("/logs/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(requestData)
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const tableBody = document.getElementById("logsTable").querySelector("tbody");
            tableBody.innerHTML = ""; // Очистить таблицу перед заполнением

            data.forEach(log => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${log.id}</td>
                    <!--<td>${log.guide}</td>-->
                    <td>${log.user_name}</td>
                    <!--<td>${log.devise_guid}</td>-->
                    <!--<td>${log.department_id}</td>-->
                    <td>${log.inout}</td>
                    <td>${log.response}</td>
                    <!--<td>${log.json_data}</td>-->
                    <td>${new Date(log.created_at + 'Z').toLocaleString()}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error("Ошибка:", error));
});



function showCenteredBlock(text) {

    const block = document.createElement('div');
    block.textContent = text;
    block.classList.add('messBlock');

    document.body.appendChild(block);
    setTimeout(() => {
        block.remove();
    }, 4000);
}
