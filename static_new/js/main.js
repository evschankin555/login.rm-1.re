


function setCookie(name, value, days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = "expires=" + date.toString();
    document.cookie = name + "=" + encodeURIComponent(JSON.stringify(value)) + ";" + expires + ";path=/";
 }


 function getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');

    for (let i = 0; i < ca.length; i++) {
        let c = ca[i].trim();  // убираем пробелы по краям

        if (c.indexOf(nameEQ) === 0) {
            let cookieValue = c.substring(nameEQ.length, c.length);

            // Проверка, что значение существует и не является пустой строкой
            if (cookieValue) {
                try {
                    return JSON.parse(decodeURIComponent(cookieValue));
                } catch (e) {
                    console.error('Неверно переданный параметр:', e);
                    return null;  // Если ошибка, возвращаем null
                }
            }
        }
    }

    return null;  // Если cookie не найдено
}


function deleteCookie(name) {
    // Устанавливаем куки с прошедшей датой
    document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
}

function update_device() {
    var device = getCookie('device')
    if (device) {
        device_id = device.device_id;
    }
    fetch('/get_device_id', {
        method: 'POST',
        body: JSON.stringify({ device_id: device_id}),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            let device_data = data.device
            console.log(device_data.id)
            setCookie('device', {'device_id': device_data.id}, 30)
            device_id = device_data.id

            let division = getCookie('division')
            if (division) {
                if (device_data.department != division.department_guid) {
                    // в целом, можно найти нужный департамент, если data.device_id не пустая и записать в куки актуальный data.device_id
                    deleteCookie('division');

                    try {
                        setDivision && setDivision();
                    } catch (error) {
                        console.error("Ошибка при выполнении функции:", error);
                    }
                }
            }
        }
        else {
            console.error('Error:', '/get_device_id')
        }
    })
    .catch(error => console.error('Error:', error))
    .finally(() => {});
}


var device_id;

