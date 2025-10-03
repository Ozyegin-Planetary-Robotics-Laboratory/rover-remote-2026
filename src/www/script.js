// Windows
const screens = [{
        id: "Blank",
        html: `
      <div class="BlankScreenClass">
        <span class="SelectScreenSpanClass">Select a screen</span
      </div>
    `
    },
    // { id: "MobileScreen",
    //   html: `
    //     <div id="MobileScreen">
    //       <div class="header">

    //         <div class="control-panel">
    //           <button id="emergency-btn">EMERGENCY STOP</button>
    //           <button id="connect-btn">CONNECT</button>
    //         </div>
    //       </div>
    //       <div id="joystick-container">
    //         <div class="horizontal-axis"></div>
    //         <div class="vertical-axis"></div>
    //         <div id="joystick-knob">STOP</div>
    //       </div>

    //       <div id="colorpicker-container">
    //         <input type="text" id="html5colorpicker" onchange="clickColor(0, -1, -1, 5)" value=""
    //           style="width:60%;height:15%;">
    //         <input type="text" id="html5armcom" onchange="clickColor(0, -1, -1, 5)" value="" style="width:60%;height:15%;">
    //         <input type="text" id="motorparam" onchange="clickColor(0, -1, -1, 5)" value="" style="width:60%;height:15%;">
    //       </div>
    //       <input type="checkbox" id='kolkontrol'></input>
    //       <div class="footer">
    //         <div id="output">X: 0.00, Y: 0.00</div>
    //         <div id="ConnectionStatus">Not connected</div>
    //         <div class="settings">
    //           <label for="ip-address">Bridge IP Address:</label>
    //           <input type="text" id="ip-address" value="192.168.1.3">
    //           <label for="port">Bridge WebSocket Port:</label>
    //           <input type="number" id="port" value="8765">
    //         </div>
    //       </div>
    //     </div>
    //   `
    // },
    {
        id: "CameraScreen",
        html: `
        <div class="CameraContainer" id="video-container">

        <div class="video-block">
          <canvas class="vid" id="video-canvas" crossorigin="anonymous"></canvas>
          <div class="CameraControlsDiv">
            <button class="ButtonClass" style="margin-top: 200px" onclick="moveLeft(this)"><</button>
            <button class="ButtonClass" style="margin-top: 200px" onclick="moveRight(this)">></button>
            <button class="ButtonClass" style="margin-top: 200px" onclick="CameraRotate('')">🔃</button>
            <button class="ButtonClass" style="margin-top: 200px" onclick="document.getElementById('video-canvas').width=300">➗</button>

          </div>
        </div>

        <div class="video-block">
          <canvas class="vid" id="video-canvas2" crossorigin="anonymous"></canvas>
          <div class="CameraControlsDiv">
            <button class="ButtonClass" style="margin-top: 200px" onclick="moveLeft(this)"><</button>
            <button class="ButtonClass" style="margin-top: 200px" onclick="moveRight(this)">></button>
            <button class="ButtonClass" style="margin-top: 200px" onclick="CameraRotate(2)">🔃</button>
            <button class="ButtonClass" style="margin-top: 200px" onclick="document.getElementById('video-canvas2').width=300">➗</button>

          </div>
        </div>

        <div class="video-block">
          <canvas class="vid" id="video-canvas3" crossorigin="anonymous"></canvas>
          <div class="CameraControlsDiv">
            <button class="ButtonClass" style="margin-top: 200px" onclick="moveLeft(this)"><</button>
            <button class="ButtonClass" style="margin-top: 200px" onclick="moveRight(this)">></button>
            <button class="ButtonClass" style="margin-top: 200px" onclick="CameraRotate(3)">🔃</button>
            <button class="ButtonClass" style="margin-top: 200px" onclick="document.getElementById('video-canvas3').width=300">➗</button>

        </div>
    `,
    },
    {
        id: "ControllerScreen",
        html: `
    <div id="ControllerScreen">
     <div onclick="PrintControllerId()" id="PlayerNumber"></div>

     <div id=ControllerScreenButtons></div>
    </div>
    `
    },
    {
        id: "StatusScreen",
        html: `
    <div id="StatusScreen">
      <div id="RoverStatusDiv">
        <div class="RoverStatusSectionClass" id="LocoStatusDiv">
          <div class="LocoStatusSideClass" style="margin-right: 1rem;">
            <div class="LocoStatusDivClass">
              <span id="LocoStatusTemp1" class="LocoStatusSpanClass LocoStatusTempratureSpanClass"></span>
              <span id="LocoStatusSpeed1" class="LocoStatusSpanClass LocoStatusSpeedSpanClass"></span>
            </div>
            <button id="SwitchLocoHorizontal" onclick="SwitchLocoMotors('horizontal')" class="ButtonClass SwitchButtonClass"><img class="SwitchIconClass" src="icons/SwitchArrows.png"></button>
            <div class="LocoStatusDivClass">
              <span id="LocoStatusTemp3" class="LocoStatusSpanClass LocoStatusTempratureSpanClass"></span>
              <span id="LocoStatusSpeed3" class="LocoStatusSpanClass LocoStatusSpeedSpanClass"></span>
            </div>
          </div>

          <div id="RoverStatusImg">
            <img id="EmergencyButton" style="width: 5rem;" src="icons/EmergencyButton.png"></img>
          </div>

          <div class="LocoStatusSideClass" style="margin-left: 1rem;">
            <div style="justify-content: start;" class="LocoStatusDivClass">
              <span id="LocoStatusTemp2" class="LocoStatusSpanClass LocoStatusTempratureSpanClass"></span>
              <span id="LocoStatusSpeed2" class="LocoStatusSpanClass LocoStatusSpeedSpanClass"></span>
            </div>
            <button id="SwitchLocoVertical" onclick="SwitchLocoMotors('vertical')" class="ButtonClass SwitchButtonClass"><img style="transform: rotate(90deg);" class="SwitchIconClass" src="icons/SwitchArrows.png"></button>
            <div style="justify-content: end;" class="LocoStatusDivClass">
              <span id="LocoStatusTemp4" class="LocoStatusSpanClass LocoStatusTempratureSpanClass"></span>
              <span id="LocoStatusSpeed4" class="LocoStatusSpanClass LocoStatusSpeedSpanClass"></span>
            </div>
          </div>

        </div>
        <div class="RoverStatusSectionClass" id="ConnectionStatusDiv">
          <span style="margin-bottom: 1rem;">Connection</span>
          <button onclick="connectToBridge()" style="background-color: var(--color-blue)" class="ButtonClass">Connect</button>
          <button onclick="disconnectFromBridge()" style="background-color: var(--color-red); margin-top: 1rem;" class="ButtonClass">Disconnect</button>
        </div>
        <div class="RoverStatusSectionClass" id="LedControlDiv">
          <span>Colors</span>
          <div>
            <button id="LedButton0" onclick="LedChangeColor('0')" style="background-color: black;" class="LedButtonClass">❌</button>
            <button id="LedButton1" onclick="LedChangeColor('1')" style="background-color: var(--color-red);" class="LedButtonClass"></button>
            <button id="LedButton2" onclick="LedChangeColor('2')" style="background-color: var(--color-green);" class="LedButtonClass"></button>
            <button id="LedButton3" onclick="LedChangeColor('3')" style="background-color: var(--color-blue);" class="LedButtonClass"></button>
            <button id="LedButton4" onclick="LedChangeColor('4')" style="background-color: var(--color-yellow);" class="LedButtonClass"></button>
            <button id="LedButton5" onclick="LedChangeColor('5')" style="background-color: var(--color-pink);" class="LedButtonClass"></button>
            <button id="LedButton6" onclick="LedChangeColor('6')" style="background-color: var(--color-cyan);" class="LedButtonClass"></button>
          </div>
        </div>
        <div class="RoverStatusSectionClass" id="SpeedControlDiv">
          <span>Speed Control</span>
          <div style="padding: 1rem 0rem;">
            <div>
              <span>Loco Speed</span>
              <div id="LocoSpeedValue" class="SpeedControlValueDiv">-</div>
              <input step="0.1" min="0" max="2" id="LocoSpeedSlider" oninput="SpeedControl('Loco', this.value)" style="margin: 1rem 0;" class="SliderClass" type="range">
            </div>
            <div style="margin-top: 1rem;">
              <span>Manipulator Speed</span>
              <div id="ManipulatorSpeedValue" class="SpeedControlValueDiv">-</div>
              <input step="0.1" min="0" max="5" id="ManipulatorSpeedSlider" oninput="SpeedControl('Manipulator', this.value)" style="margin: 1rem 0;" class="SliderClass" type="range">
            </div>
          </div>
        </div>
      </div>
    </div>
    `,
    },
    {
        id: "ManipulatorScreen",
        html: `
    <div id="ManipulatorScreen">
      <div id="ManipulatorContainer">
        <div style="margin-top: 400px" id="ManipulatorDOF1" class="ManipulatorDOFClass">
          <div class="joint-circle"></div>
          <div id="ManipulatorLink1" class="ManipulatorLinkClass" style="width:150px;">
            <div id="ManipulatorDOF2" class="ManipulatorDOFClass" style="position:absolute; left:150px; top:0;">
              <div class="joint-circle"></div>
              <div id="ManipulatorLink2" class="ManipulatorLinkClass" style="width:100px;">
                <div id="ManipulatorDOF3" class="ManipulatorDOFClass" style="position:absolute; left:100px; top:0;">
                  <div class="joint-circle"></div>
                  <div id="ManipulatorLink3" class="ManipulatorLinkClass" style="width:50px;"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
     </div>

    </div>
    `
    },
    {
        id: "PanTiltScreen",
        html: `
    <div id="PanTiltScreen">
      <div class="PanTiltContainer">
        <div id="RoverImgPanTilt">
          <img id="PanTiltUp" class="PanTiltCameraClass" src="icons/Camera.png"></img>
        </div>
      </div>
      <div id="PantiltSideDiv" class="PanTiltContainer">
        <img id="Side" class="PanTiltCameraClass" src="icons/Camera.png"></img>
        <img id="RoverSideImg" src="icons/RoverSide.png"></img>
      </div>
    </div>
    `
    },
    {
        id: "ScienceScreen",
        html: `
    <div id="ScienceScreen">
      <div id="ScienceSensorsSection" class="RoverStatusSectionClass">
        <span class="ScienceDataSpanClass" id="LoadCell1">Load cell 1: </span>
        <span class="ScienceDataSpanClass" id="LoadCell2">Load cell 2: </span>
        <span class="ScienceDataSpanClass" id="AirHumidity">Air humidity: </span>
        <span class="ScienceDataSpanClass" id="AirTemperature">Air temperature: </span>
        <span class="ScienceDataSpanClass" id="SoilHumidity">Soil humidty: </span>
        <button onClick='ScienceCommandAdder("ScienceDown")'>Science Asagi Indirmeye Basla</button>
        <button onClick='ScienceCommandAdder("ScienceUp")'>Science Yukari Goturmeye Basla</button>
        <button onClick='ScienceCommandAdder("ScienceStop")'>Science Hareketi Durdur</button>
        <button onClick='ScienceCommandAdder("DrillStart")'>Science Matkap Dondur</button>
        <button onClick='ScienceCommandAdder("DrillStop")>Science Matkap Durdur</button>
    
      </div>
    </div>
    `

    }
]

let screenSelectBoxString = "";
CreateScreenSelectBoxString();

let windowId = 0;
const windowSizeIncrement = 10;
let currentWindows = [];

const colorConfigs = [{
        type: "latency",
        tresholds: [250, 1000],
    },
    {
        type: "temperature",
        tresholds: [45, 60],
    },
    {
        type: "speed",
        tresholds: [30, 70],
    },
];

let isResizingWindow = false;
let cursorStartX, windowStartWidth, currentResizingWindowId;

// Controller
let controllerScreenOldState = false;
const controllerDeadzone = 0.1;
const controllerDOF1Deadzone = 0.25;

let controllerId = "";
let buttonFunctionsString = "";
const commandFunctions = [
    // Loco
    { id: "LocoAngular", type: "Axis" },
    { id: "LocoLinear", type: "Axis" },

    // Science
    { id: "ScienceDown", type: "Button" },
    { id: "ScienceUp", type: "Button" },

    // Arm
    { id: "DOF1Left", type: "Button" },
    { id: "DOF1Right", type: "Button" },
    { id: "DOF1", type: "Axis" },

    { id: "DOF2Down", type: "Button" },
    { id: "DOF2Up", type: "Button" },
    { id: "DOF2", type: "Axis" },

    { id: "DOF3Down", type: "Button" },
    { id: "DOF3Up", type: "Button" },

    { id: "DOF4Down", type: "Button" },
    { id: "DOF4Up", type: "Button" },

    { id: "EndEffectorCCW", type: "Button" },
    { id: "EndEffectorCW", type: "Button" },

    { id: "GripperOpen", type: "Button" },
    { id: "GripperClose", type: "Button" },

    { id: "PanTiltDown", type: "Button" },
    { id: "PanTiltUp", type: "Button" },
    { id: "PanTiltLeft", type: "Button" },
    { id: "PanTiltRight", type: "Button" },
    
    { id: "ManipulatorSpeedIncrease", type: "Button" },
    { id: "ManipulatorSpeedDecrease", type: "Button" },


];

const controllerConfigs = [
    // PS2 Oğuzhan
    {
        ids: [
            "PS(R) Controller Adaptor (Vendor: 0e8f Product: 0003)",
            "My-Power CO.,LTD. PS(R) Controller Adaptor (STANDARD GAMEPAD Vendor: 054c Product: 0268)",
        ],
        config: [
            { button: 14, func: "ScienceDown" },
            { button: 12, func: "ScienceUp" },
            { button: 6, func: "EndEffectorCCW" },
            { button: 7, func: "EndEffectorCW" },
            { button: 4, func: "GripperOpen" },
            { button: 5, func: "GripperClose" },
            { button: 0, func: "DOF3Down" },
            { button: 2, func: "DOF3Up" },
            { button: 3, func: "DOF4Down" },
            { button: 1, func: "DOF4Up" },
            { axis: 0, func: "LocoAngular" },
            { axis: 1, func: "LocoLinear" },
            { axis: 2, func: "DOF1" },
            { axis: 3, func: "DOF2" },
        ],
    },
    // Xbox Uraz
    {
        ids: [
            "Xbox 360 Controller (XInput STANDARD GAMEPAD)",
            "HID uyumlu oyun denetleyicisi (STANDARD GAMEPAD Vendor: 045e Product: 0b13)",
            "Microsoft Controller (STANDARD GAMEPAD Vendor: 045e Product: 0b12)",
        ],
        config: [
            { button: 0, func: "PanTiltDown" },
            { button: 3, func: "PanTiltUp" },
            { button: 2, func: "PanTiltLeft" },
            { button: 1, func: "PanTiltRight" },
            { button: 4, func: "GripperOpen" },
            { button: 5, func: "GripperClose" },
            { button: 13, func: "DOF3Down" },
            { button: 12, func: "DOF3Up" },
            { button: 15, func: "DOF4Down" },
            { button: 14, func: "DOF4Up" },
            { button: 6, func: "EndEffectorCCW" },
            { button: 7, func: "EndEffectorCW" },
            { button: 8, func: "ManipulatorSpeedDecrease" },
            { button: 9, func: "ManipulatorSpeedIncrease" },
            { axis: 0, func: "LocoAngular" },
            { axis: 1, func: "LocoLinear" },
            { axis: 2, func: "DOF1" },
            { axis: 3, func: "DOF2" },
        ],
    },
    // 8bitdo Emre
    {
        ids: [
            "Windows için Xbox 360 Denetleyicisi (STANDARD GAMEPAD)",
            "8BitDo 8BitDo Ultimate 2C Wireless Controller (Vendor: 2dc8 Product: 310a)",
        ],
        config: [
            { button: 0, func: "ScienceDown" },
            { button: 3, func: "ScienceUp" },
            { button: 4, func: "GripperOpen" },
            { button: 5, func: "GripperClose" },
            { button: 13, func: "DOF3Down" },
            { button: 12, func: "DOF3Up" },
            { button: 15, func: "DOF4Down" },
            { button: 14, func: "DOF4Up" },
            { button: 6, func: "EndEffectorCCW" },
            { button: 7, func: "EndEffectorCW" },
            { axis: 0, func: "LocoAngular" },
            { axis: 1, func: "LocoLinear" },
            { axis: 2, func: "DOF1" },
            { axis: 3, func: "DOF2" },
            { axis: 8, func: "ManipulatorSpeedDecrease" },
            { axis: 9, func: "ManipulatorSpeedIncrease" },
        ],
    },
];

// StatusScreen
let targetLedColor = "";
let disableLedButtons = false;

let locoSpeed = 1;
let manipulatorSpeed = 1;
let locoMotorDirection = "";

let motorStatusData = {
    loco: [],
    arm: [],
};

// CameraScreen
var cameraPlayer1, cameraPlayer2, cameraPlayer3

// ScienceScreen
let scienceScreenOn = false
let scienceCommandStrings = []

// Connection
const connectionStatus = document.getElementById("ConnectionStatus");
const ipAdress = document.location.host.split(":")[0];
const port = 8765;
let isConnected = false;
const latencySpan = document.getElementById("LatencySpan");
let latestTimestamp = 0;

AddWindow();
SelectScreen("screenDiv1", "StatusScreen")
AddWindow();
SelectScreen("screenDiv2", "CameraScreen")

//#region FUNCTIONS

// #region Windows and Screens
function AddWindow() {
    windowId++;
    document.getElementById("WindowsDiv").innerHTML += `
    <div style="width: 100%" id="window${windowId}" class="WindowClass">
      <div class="WindowTopClass">
        <select id="WindowSelectBox${windowId}" onchange="SelectScreen('screenDiv${windowId}', this.value)" name="" class="SelectBoxClass WindowSelectBox">
          ${screenSelectBoxString}
        </select>
        <div class="WindowControlDiv">
          <button onclick="ChangeOrder('window${windowId}', -1)" class="WindowControlButtonClass"><</button>
          <button onclick="ChangeOrder('window${windowId}', 1)" class="WindowControlButtonClass">></button>
          <button onclick="CloseWindow('window${windowId}')" style="border: none;" class="WindowControlButtonClass">x</button>
        </div>
      </div>
      <div id="screenDiv${windowId}"></div>
    </div>
    <div onmousedown="WindowResizeBarMouseDown(event, 'window${windowId}')" id="WindowResizeBar${windowId}" class="WindowResizeBarClass"></div>
  `;
    currentWindows.push({ windowId: "window" + windowId, screenId: "Blank" });
    SelectScreen("screenDiv" + windowId, "Blank");
}

function WindowResizeBarMouseDown(e, windowId) {
    isResizingWindow = true;
    currentResizingWindowId = windowId;

    const windowElem = document.getElementById(windowId);

    const measuredWidth = windowElem.getBoundingClientRect().width;
    windowElem.style.width = measuredWidth + "px";
    windowElem.style.flex = "0 0 auto";

    cursorStartX = e.clientX;
    windowStartWidth = measuredWidth;

    document.addEventListener("mousemove", WindowResizeMouseMove);
    document.addEventListener("mouseup", WindowResizeMouseUp);

    e.preventDefault();
}

function WindowResizeMouseMove(e) {
    if (!isResizingWindow) return;
    const diffX = e.clientX - cursorStartX;
    let newWidth = windowStartWidth + diffX;
    if (newWidth < 150) newWidth = 150;
    document.getElementById(currentResizingWindowId).style.width =
        newWidth + "px";
}

function WindowResizeMouseUp() {
    isResizingWindow = false;
    document.removeEventListener("mousemove", WindowResizeMouseMove);
    document.removeEventListener("mouseup", WindowResizeMouseUp);
}

function GetScreenHTML(id) {
    for (let i = 0; i < screens.length; i++) {
        const screen = screens[i];
        if (screen.id == id) return screen.html;
    }
}

function CreateScreenSelectBoxString() {
    for (let i = 0; i < screens.length; i++) {
        const screen = screens[i];
        screenSelectBoxString += `<option value="${screen.id}">${screen.id}</option>\n`;
    }
}

function SelectScreen(screenDivId, screenId) {
    document.getElementById(screenDivId).innerHTML = GetScreenHTML(screenId);
    const windowId = "window" + screenDivId.slice("screenDiv".length);

    FindProperty(currentWindows, "windowId", windowId).screenId = screenId;

    if (screenId == "StatusScreen") {
        document.getElementById("LocoSpeedSlider").value = locoSpeed;
        document.getElementById("ManipulatorSpeedSlider").value =
            manipulatorSpeed;
        document.getElementById("LocoSpeedValue").textContent = locoSpeed;
        document.getElementById("ManipulatorSpeedValue").textContent =
            manipulatorSpeed;
    } else if (screenId == "CameraScreen") {
        setTimeout(() => {
            let canvas = document.getElementById("video-canvas");
            let url = "ws://" + document.location.hostname + ":8082/";
            cameraPlayer1 = new JSMpeg.Player(url, { canvas: canvas });

            let canvas2 = document.getElementById("video-canvas2");
            let url2 = "ws://" + document.location.hostname + ":8084/";
            cameraPlayer2 = new JSMpeg.Player(url2, { canvas: canvas2 });

            let canvas3 = document.getElementById('video-canvas3');
            let url3 = 'ws://' + document.location.hostname + ':8086/';
            cameraPlayer3 = new JSMpeg.Player(url3, { canvas: canvas3 });
        }, 2000);
    } else if (screenId == "ScienceScreen") {
        scienceScreenOn = true
    }

    UpdateScreenSelectBoxOptions()
}

function UpdateScreenSelectBoxOptions() {
    for (let a = 0; a < currentWindows.length; a++) {
        const window = currentWindows[a];
        const selectboxId =
            "WindowSelectBox" + window.windowId.slice("window".length);
        const children = document.getElementById(selectboxId).children;

        for (let i = 0; i < children.length; i++) {
            const option = children[i];

            if (
                option.value != "Blank" &&
                window.screenId != option.value &&
                FindProperty(currentWindows, "screenId", option.value)
            ) {
                option.disabled = true;
            }
            // After some changes the value of the selectbox started to change when a new window is added.
            // I have no idea why. The else if condition below is for temporary fix.
            else if (window.screenId == option.value) {
                option.selected = true;
            } else {
                option.disabled = false;
            }
        }
    }
}

// function ChangeWindowSize(id, size) {
//   const targetWindow = document.getElementById(id)
//   console.log(parseInt(targetWindow.style.width.slice(0, -1)) + windowSizeIncrement * size)
//   targetWindow.style.width = (parseInt(targetWindow.style.width.slice(0, -1)) + windowSizeIncrement * size) + "%";
// }

function CloseWindow(id) {
    document.getElementById(id).remove();
    const windowResizeBarId = "WindowResizeBar" + id.slice("window".length);
    document.getElementById(windowResizeBarId).remove();

    const index = currentWindows.indexOf(id);
    currentWindows.splice(index, 1);

    UpdateScreenSelectBoxOptions();
}

function ChangeOrder(id, direction) {
    if (currentWindows.length <= 1) return;
    const window = FindProperty(currentWindows, "windowId", id);
    const index = currentWindows.indexOf(window);

    if (index == 0 && direction < 0) return;
    else if ((index == currentWindows.length - 1) & (direction > 1)) return;

    currentWindows.splice(index, 1);
    currentWindows.splice(index + direction, 0, window);

    for (let i = 0; i < currentWindows.length; i++) {
        const windowId = currentWindows[i].windowId;
        const window = document.getElementById(windowId);
        const windowResizeBarId =
            "WindowResizeBar" + windowId.slice("window".length);
        const windowResizeBar = document.getElementById(windowResizeBarId);

        const flexIndex = (i + 1) * 2;

        window.style.order = flexIndex;
        windowResizeBar.style.order = flexIndex + 1;
    }
}

//#endregion

//#region ControllerScreen
CreateButtonFunctionsString();

function CreateButtonFunctionsString() {
    buttonFunctionsString += '<option value="none">none</option>\n';
    for (let i = 0; i < commandFunctions.length; i++) {
        const func = commandFunctions[i];
        buttonFunctionsString += `
    <option value="${func.id}">${func.id}</option>\n
    `;
    }
}

function PrintControllerId() {
    console.log(controllerId);
}

function GetControllerConfigFunction(type, id) {
    for (let i = 0; i < controllerConfigs.length; i++) {
        const controllerConfig = controllerConfigs[i];
        if (controllerConfig.ids.includes(controllerId)) {
            const config = controllerConfig.config;
            const subConfig = FindProperty(config, type, id);
            return subConfig != undefined ? subConfig.func : "none";
        }
    }
}
//#endregion

//#region ManipulatorScreen
// updateArm(45,-45,-45)
function updateArm(dof2, dof3, dof4) {
    document.getElementById("ManipulatorDOF1").style.transform =
        `rotate(${dof2}deg)`;
    document.getElementById("ManipulatorDOF2").style.transform =
        `rotate(${dof3}deg)`;
    document.getElementById("ManipulatorDOF3").style.transform =
        `rotate(${dof4}deg)`;
}

//#endregion

//#region StatusScreen
function UpdateRoverStatus() {
    for (let i = 0; i < motorStatusData.loco.length; i++) {
        const temp = motorStatusData.loco[i].temp.toFixed(0);
        const locoStatusTemp = document.getElementById(
            "LocoStatusTemp" + (i + 1),
        );
        locoStatusTemp.textContent = temp;
        locoStatusTemp.style.color = ColorCalculator("temperature", temp);
        locoStatusTemp.title = motorStatusData.loco[i].Port;

        const speed = (
            (motorStatusData.loco[i].Velocity * 60) /
            (2 * Math.PI)
        ).toFixed(0);
        const locoStatusSpeed = document.getElementById(
            "LocoStatusSpeed" + (i + 1),
        );
        locoStatusSpeed.textContent = speed;
        locoStatusSpeed.style.color = ColorCalculator("speed", speed);
    }
}

function LedChangeColor(color) {
    if (disableLedButtons) return;
    targetLedColor = color;
    LedButtonStateChanger(false);
    disableLedButtons = true;

    for (let i = 1; i <= 6; i++) {
        document.getElementById("LedButton" + i).style.border =
            "3px solid transparent";
    }
    document.getElementById("LedButton" + color).style.border =
        "3px solid white";

    setTimeout(() => {
        disableLedButtons = false;
        LedButtonStateChanger(true);
    }, 1000);
}

function LedButtonStateChanger(enabled) {
    const ledButtons = document.getElementsByClassName("LedButtonClass");
    for (let i = 0; i < ledButtons.length; i++) {
        const led = ledButtons[i];
        if (enabled) {
            led.classList.remove("LedButtonDeactivatedClass");
        } else {
            led.classList.add("LedButtonDeactivatedClass");
        }
    }
}

function SpeedControl(type, value) {
    document.getElementById(type + "SpeedValue").textContent = value;
    if (type == "Loco") {
        locoSpeed = parseFloat(value);
        document.getElementById("LocoSpeedSlider").value = value;
    } else if (type == "Manipulator") {
        manipulatorSpeed = parseFloat(value);
        document.getElementById("ManipulatorSpeedSlider").value = value;
    }
}

function SpeedControlIncremental(type, increment) {
    if (type == "Loco") {
        const locoSpeedSlider = document.getElementById("LocoSpeedSlider");
        locoSpeed += increment;
        if (locoSpeed > parseFloat(locoSpeedSlider.max))
            locoSpeed = parseFloat(locoSpeedSlider.max);
        if (locoSpeed < 0) locoSpeed = 0;
        SpeedControl("Loco", locoSpeed);
    } else if (type == "Manipulator") {
        const manipulatorSpeedSlider = document.getElementById(
            "ManipulatorSpeedSlider",
        );
        manipulatorSpeed += increment;
        if (manipulatorSpeed > parseFloat(manipulatorSpeedSlider.max))
            manipulatorSpeed = parseFloat(manipulatorSpeedSlider.max);
        if (manipulatorSpeed < 0) manipulatorSpeed = 0;
        SpeedControl("Manipulator", manipulatorSpeed);
    }
}

function SwitchLocoMotors(direction) {
    let horizontal = false;
    let vertical = false;

    if (locoMotorDirection.includes("h")) horizontal = true;
    if (locoMotorDirection.includes("v")) vertical = true;

    if (direction == "horizontal") horizontal = !horizontal;
    if (direction == "vertical") vertical = !vertical;

    if (horizontal && !vertical) locoMotorDirection = "h";
    else if (!horizontal && vertical) locoMotorDirection = "v";
    else if (horizontal && vertical) locoMotorDirection = "hv";
    else locoMotorDirection = "";

    document.getElementById("SwitchLocoHorizontal").style.backgroundColor =
        "var(--color2)";
    document.getElementById("SwitchLocoVertical").style.backgroundColor =
        "var(--color2)";
    if (horizontal)
        document.getElementById("SwitchLocoHorizontal").style.backgroundColor =
        "var(--color-blue)";
    if (vertical)
        document.getElementById("SwitchLocoVertical").style.backgroundColor =
        "var(--color-blue)";
}
//#endregion

//#region CameraScreen
function moveLeft(button) {
    const block = button.closest(".video-block");
    const prev = block.previousElementSibling;
    if (prev) {
        block.parentNode.insertBefore(block, prev);
    }
}

function moveRight(button) {
    const block = button.closest(".video-block");
    const next = block.nextElementSibling;
    if (next) {
        block.parentNode.insertBefore(next, block);
    }
}

function downloadCanvas(canvas, filename) {
    const image = canvas.toDataURL("image/png");
    const a = document.createElement("a");
    a.href = image;
    a.download = filename;
    a.click();
}

function downloadAllCanvases() {
    const canvas1 = document.getElementById("video-canvas");
    const canvas2 = document.getElementById("video-canvas2");
    const canvas3 = document.getElementById("video-canvas3");
    if (canvas1) downloadCanvas(canvas1, "frame1.png");
    if (canvas2) downloadCanvas(canvas2, "frame2.png");
    if (canvas3) downloadCanvas(canvas3, "frame3.png");
}

function CameraRotate(cam) {
  const el = document.getElementById("video-canvas" + cam);

  // If not already set, start at 0
  let angle = el.dataset.rotation ? parseInt(el.dataset.rotation) : 0;
  
  // Add 90 degrees
  angle = (angle + 90) % 360; // keeps it in [0,360)
  
  // Save the new angle
  el.dataset.rotation = angle;
  
  // Apply rotation
  el.style.transform = `rotate(${angle}deg)`;
}
//#endregion

//#region Connection

function connectToBridge() {
    reconnectAttempts = 0;

    try {
        // Create WebSocket connection
        connectionStatus.textContent = `Connecting to bridge at ${ipAdress}:${port}...`;

        // Use WebSocket protocol (ws:// or wss:// for secure)
        socket = new WebSocket(`ws://${ipAdress}:${port}`);

        // Connection opened
        socket.addEventListener("open", function(event) {
            isConnected = true;
            connectionStatus.textContent = `Connected to bridge at ${ipAdress}:${port}`;
            connectionStatus.classList.add("connected");
            // connectBtn.textContent = "DISCONNECT";
            // connectBtn.classList.add("connected");

            // Start sending joystick data
            // startSendingData();
        });

        // Listen for messages from the server
        socket.addEventListener("message", function(event) {
            try {
                const response = JSON.parse(event.data);
                // console.log('Message from bridge:', response);
                latestTimestamp = response.timestamp;
                // Handle different response types
                if (response.status === "connected") {
                    console.log("Connection confirmed by bridge");
                    connectionStatus.textContent = "Connected";
                    connectionStatus.classList.add("connected");
                } else if (response.status === "still_connected") {
                    motorStatusData.loco = response.message.loco;
                    if (response.message.crash) {
                        //alert("EYVAH!")
                        console.log("eyvah!");
                    }

                    const scienceData = response.message.science
                    if (scienceScreenOn && scienceData) {
                        document.getElementById("LoadCell1").textContent = scienceData.loadCell1
                        document.getElementById("LoadCell2").textContent = scienceData.loadCell2
                        document.getElementById("AirHumidity").textContent = scienceData.airHumidity
                        document.getElementById("AirTemperature").textContent = scienceData.airTemperature
                        document.getElementById("SoilHumidity").textContent = scienceData.soilHumidity
                    }
                } else if (response.status === "sent") {
                    // Data was successfully sent to the rover
                    connectionStatus.textContent = `Sent: Linear=${response.linear.toFixed(2)}, Angular=${response.angular.toFixed(2)}`;
                } else if (response.status === "emergency_stop_sent") {
                    connectionStatus.textContent =
                        "Emergency stop sent to rover";
                } else if (response.status === "resume_control_acknowledged") {
                    connectionStatus.textContent = "Control resumed";
                } else if (response.status === "error") {
                    console.error("Error from bridge:", response.message);
                    connectionStatus.textContent = `Error: ${response.message}`;
                }
            } catch (error) {
                console.error("Error parsing bridge response:", error);
            }
        });

        // Connection closed
        // socket.addEventListener('close', function (event) {
        //   if (isConnected) {
        //     isConnected = false;
        //     connectionStatus.textContent = `Connection closed: ${event.reason || 'Unknown reason'}`;
        //     connectionStatus.classList.remove('connected');
        //     // connectBtn.textContent = 'CONNECT';
        //     // connectBtn.classList.remove('connected');

        //     // if (sendInterval) {
        //     //   clearInterval(sendInterval);
        //     //   sendInterval = null;
        //     // }

        //     // if (pingInterval) {
        //     //   clearInterval(pingInterval);
        //     //   pingInterval = null;
        //     // }

        //     // Try to reconnect if not manually disconnected
        //     // if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        //     //   reconnectAttempts++;
        //     //   connectionStatus.textContent = `Connection lost. Reconnecting (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`;
        //     //   setTimeout(connectToBridge, 2000); // Try to reconnect after 2 seconds
        //     // }
        //   }
        // });

        // Connection error
        socket.addEventListener("error", function(error) {
            connectionStatus.textContent = `Connection error`;
            console.error("WebSocket error:", error);
        });
    } catch (error) {
        connectionStatus.textContent = `Connection failed: ${error.message}`;
        console.error("Connection error:", error);
    }
}

function disconnectFromBridge() {
    // if (sendInterval) {
    //   clearInterval(sendInterval);
    //   sendInterval = null;
    // }

    // if (pingInterval) {
    //   clearInterval(pingInterval);
    //   pingInterval = null;
    // }

    if (socket) {
        // Send a clean disconnect message if possible
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(
                JSON.stringify({
                    command: "disconnect",
                    message: "User initiated disconnect",
                }),
            );
        }

        // Close the socket
        socket.close(1000, "User disconnected");
        socket = null;
    }

    isConnected = false;
    connectionStatus.textContent = "Disconnected";
    connectionStatus.classList.remove("connected");
    reconnectAttempts = 0;
}
//#endregion

//#region General Functions
function FindProperty(array, property, value) {
    for (let i = 0; i < array.length; i++) {
        const element = array[i];
        if (element[property] == value) return element;
    }
}

function ColorCalculator(type, value) {
    const tresholds = FindProperty(colorConfigs, "type", type).tresholds;

    if (tresholds[0] >= value) return "var(--color-green)";
    else if (tresholds[1] >= value && value > tresholds[0])
        return "var(--color-yellow)";
    else if (value > tresholds[1]) return "var(--color-red)";
}
//#endregion

function ScienceCommandAdder(command) {
    if (!scienceCommandStrings.includes(command)) {
        scienceCommandStrings.push(command)
    }
}

//#endregion

// Gamepad
setInterval(() => {
    scienceCommandStrings = []
        // console.log(navigator.getGamepads())
    const gamepads = navigator.getGamepads();
    const playerNumberElement = document.getElementById("PlayerNumber");
    const ControllerScreenButtonsElement = document.getElementById(
        "ControllerScreenButtons",
    );
    let currentGamepad = null;
    let controllerCount = 0;
    let controllerChanged = false;
    let controllerScreenOn =
        FindProperty(currentWindows, "screenId", "ControllerScreen") !=
        undefined;
    let statusScreenOn =
        FindProperty(currentWindows, "screenId", "StatusScreen") != undefined;

    // player number
    for (let i = 0; i < gamepads.length; i++) {
        const gamepad = gamepads[i];
        if (gamepad != null) {
            controllerCount++;

            if (controllerScreenOn) {
                playerNumberElement.textContent = "P" + (i + 1);
                playerNumberElement.style.color = "var(--color-green)";
            }

            currentGamepad = gamepad;
            if (controllerId != gamepad.id) {
                controllerId = gamepad.id;
                controllerChanged = true;
            } else {
                controllerChanged = false;
            }
        }
    }

    if (!controllerScreenOldState && controllerScreenOn)
        controllerChanged = true;

    if (controllerScreenOn) {
        controllerScreenOldState = true;
        if (controllerCount == 0) {
            playerNumberElement.textContent = "None";
            playerNumberElement.style.color = "var(--color-red)";
            playerNumberElement.title = "None";
            ControllerScreenButtonsElement.innerHTML = "<span>Buttons</span>";
            return;
        } else if (controllerCount > 1) {
            playerNumberElement.textContent = "Multiple";
            playerNumberElement.style.color = "var(--color-yellow)";
        }

        // buttons
        if (controllerChanged) {
            ControllerScreenButtonsElement.innerHTML = "<span>Buttons</span>";
        }

        for (let a = 0; a < currentGamepad.buttons.length; a++) {
            const button = currentGamepad.buttons[a];
            if (controllerChanged) {
                // create buttons
                ControllerScreenButtonsElement.innerHTML += `
          <div>
          <button id="controllerButton${a}" class="ButtonClass">${a}</button>
          <select id="controllerSelectBoxButton${a}" class='SelectBoxClass'>${buttonFunctionsString}</select>
          </div>
        `;
                setTimeout(() => {
                    document.getElementById(
                        "controllerSelectBoxButton" + a,
                    ).value = GetControllerConfigFunction("button", a);
                }, 250);
            }

            const controllerButton = document.getElementById(
                "controllerButton" + a,
            );
            if (button.pressed)
                controllerButton.classList.add("ControlButtonActiveClass");
            else controllerButton.classList.remove("ControlButtonActiveClass");
            controllerButton.textContent = a + ": " + button.value.toFixed(4);
        }

        // axes
        if (controllerChanged) {
            ControllerScreenButtonsElement.innerHTML += "<span>Axes</span>";
        }

        for (let a = 0; a < currentGamepad.axes.length; a++) {
            const axis = currentGamepad.axes[a];
            if (controllerChanged) {
                // create buttons
                ControllerScreenButtonsElement.innerHTML += `
          <div>
          <button id="controllerAxis${a}" class="ButtonClass">${a}</button>
          <select id="controllerSelectBoxAxis${a}" class='SelectBoxClass'>"${buttonFunctionsString}</select>
          </div>
        `;
                setTimeout(() => {
                    document.getElementById(
                        "controllerSelectBoxAxis" + a,
                    ).value = GetControllerConfigFunction("axis", a);
                }, 250);
            }
            const controllerAxis = document.getElementById(
                "controllerAxis" + a,
            );
            controllerAxis.textContent = a + ": " + axis.toFixed(4);
        }
    } else {
        controllerScreenOldState = false;
    }

    let currentCommandStrings = [];

    if (currentGamepad != null) {
        // Button Func
        for (let i = 0; i < currentGamepad.buttons.length; i++) {
            let button = currentGamepad.buttons[i];
            let buttonValue = button.value;
            if (!button.pressed) continue;

            const configFunction = GetControllerConfigFunction("button", i);
            if (configFunction == "ManipulatorSpeedIncrease") {
                if (manipulatorSpeed == 100) continue;
                SpeedControlIncremental("Manipulator", 0.25);
                continue;
            } else if (configFunction == "ManipulatorSpeedDecrease") {
                if (manipulatorSpeed == 0) continue;
                SpeedControlIncremental("Manipulator", -0.25);
                continue;
            }

            if (
                configFunction.includes("DOF") ||
                configFunction.includes("EndEffector")
            ) {
                buttonValue *= manipulatorSpeed;
            }

            const commandString = configFunction + "#" + buttonValue.toFixed(4);
            currentCommandStrings.push(commandString);
        }

        // Axis Func
        for (let i = 0; i < currentGamepad.axes.length; i++) {
            let axis = currentGamepad.axes[i];
            if (Math.abs(axis) < controllerDeadzone) continue;

            const configFunction = GetControllerConfigFunction("axis", i);
            let parameter = "";

            if (configFunction == "DOF1") {
                if (Math.abs(axis) < controllerDOF1Deadzone) continue;
            }
            if (
                configFunction == "LocoLinear" ||
                configFunction == "LocoAngular"
            ) {
                parameter = locoMotorDirection;
                axis *= locoSpeed;
            }
            if (
                configFunction.includes("DOF") ||
                configFunction.includes("EndEffector")
            ) {
                axis *= manipulatorSpeed;
            }

            const commandString =
                configFunction + "#" + axis.toFixed(4) + "#" + parameter;

            currentCommandStrings.push(commandString);
        }
    } else {
        // what to do if no controller
    }

    // console.log(currentCommandStrings);

    currentCommandStrings = currentCommandStrings.concat(scienceCommandStrings)

    //send commmands
    if (isConnected) {
        // Latency
        const currentTime = new Date().getTime();
        const latency = currentTime - latestTimestamp;
        latencySpan.textContent = latency;
        latencySpan.style.color = ColorCalculator("latency", latency);

        if (targetLedColor != "") {
            currentCommandStrings.push("Led#" + targetLedColor);
            targetLedColor = "";
        }

        // if(currentCommandStrings.length > 0) console.log(currentCommandStrings);

        socket.send(
            JSON.stringify({
                commands: currentCommandStrings,
                timestamp: Date.now(),
            }),
        );
    } else {
        latencySpan.textContent = "-";
        latencySpan.style.color = "white";
    }

    if (statusScreenOn) {
        UpdateRoverStatus();
    }

    // console.log(currentGamepad);
}, 100);
