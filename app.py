from flask import Flask, jsonify, request, render_template
import serial
import time
import serial.tools.list_ports

# Flaskアプリ
app = Flask(__name__)

# シリアルポートの状態を保持する変数
ser = None
is_connected = False
log = []

# 利用可能なシリアルポートのリストを取得
def get_serial_ports():
    ports = [port.device for port in serial.tools.list_ports.comports()]
    return ports

# シリアルポートに接続する
def connect_serial(port, baudrate, databits, parity, stopbits):
    global ser
    global is_connected
    try:
        parity_map = {'none': serial.PARITY_NONE, 'even': serial.PARITY_EVEN, 'odd': serial.PARITY_ODD}
        stopbits_map = {'1': serial.STOPBITS_ONE, '2': serial.STOPBITS_TWO}
        databits_map = {'7': serial.SEVENBITS, '8': serial.EIGHTBITS}

        ser = serial.Serial(
            port=port,
            baudrate=int(baudrate),
            bytesize=databits_map.get(databits, serial.EIGHTBITS),
            parity=parity_map.get(parity, serial.PARITY_NONE),
            stopbits=stopbits_map.get(stopbits, serial.STOPBITS_ONE),
            timeout=1  # 必要に応じて調整
        )
        is_connected = True
        return True, f"Connected to {port} at {baudrate}."
    except serial.SerialException as e:
        is_connected = False
        ser = None
        return False, f"Could not connect to {port}: {e}"

# シリアルポートから切断する
def disconnect_serial():
    global ser
    global is_connected
    if ser and ser.is_open:
        ser.close()
    ser = None
    is_connected = False
    return True, "Disconnected."

@app.route('/', methods=['POST'])
def index():
    global is_connected, log

    response = '\n'.join(log)  # 初期表示内容（ログ）

    # 固定設定値（UI用）
    ssid = "MegaChips"
    password = "12345678"
    encryption = "SAE"
    bssid = "00.00.00.00.00.00"
    ip_mode = False  # (True: DHCP, False: STATIC)
    ip_mode_display = "STATIC" if not ip_mode else "DHCP"
    ip = "10.42.0.2"
    netmask = "255.255.255.0"
    gateway = "10.42.0.1"
    dns = "8.8.8.8"
    host = "10.42.0.1"
    tcp_port = 5000
    udp_port = 5001
    send_data = "mega1234"
    socket_id = -1

    # 使用可能なシリアルポートを取得
    ports = get_serial_ports()

    return render_template('index.html',
                           response=response,
                           serial_ports=ports,
                           is_connected=is_connected,
                           ssid=ssid,
                           password=password,
                           encryption=encryption,
                           bssid=bssid,
                           ip_mode_display=ip_mode_display,
                           ip=ip,
                           netmask=netmask,
                           gateway=gateway,
                           dns=dns,
                           host=host,
                           tcp_port=tcp_port,
                           udp_port=udp_port,
                           send_data=send_data,
                           socket_id=socket_id)


# 接続/切断ボタン押下時の処理
@app.route('/uartConnect', methods=['POST'])
def uartConnect():
    global is_connected
    port = request.form.get('port')
    baudrate = request.form.get('baudrate')
    databits = request.form.get('databits')
    parity = request.form.get('parity')
    stopbits = request.form.get('stopbits')
    connected_str = request.form.get('connected')
    should_connect = connected_str.lower() == 'true'

    if should_connect and not is_connected:
        success, message = connect_serial(port, baudrate, databits, parity, stopbits)
        return jsonify({'success': success, 'message': message, 'connected': is_connected})
    elif not should_connect and is_connected:
        success, message = disconnect_serial()
        return jsonify({'success': success, 'message': message, 'connected': is_connected})
    else:
        return jsonify({'success': True, 'message': f"Connection state is already {'connected' if is_connected else 'disconnected'}.", 'connected': is_connected})

# データー送信時の処理
@app.route('/uartSend', methods=['POST'])
def uartSend():
    global ser
    if 'terminalInput' in request.form:
        cmd = request.form['terminalInput']
        if ser and ser.is_open and cmd:
            ser.write((cmd + '\n').encode('utf-8'))
            time.sleep(0.1)
            lines = []
            while True:
                line = ser.readline()
                if not line:
                    break
                lines.append(line.decode('utf-8', errors='ignore').strip())
            return '\n'.join(lines)
        else:
            return "未接続か未入力です。"
    return "不正なリクエストです。"

if __name__ == '__main__':
    # print("Available serial ports:", get_serial_ports())
    app.run(host='0.0.0.0', port=5000, debug=False)