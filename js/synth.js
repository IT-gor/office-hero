let context = new AudioContext();
let masterGain = context.createGain();

let oscillators = [[], []];
let velocityVolumes = [[], []];

let octaveShifter = 60;

masterGain.connect(context.destination);

function controlChange(controllerNr, value) {
    // do something...
}

function pitchBend(LSB, HSB) {
    // do something...
}


  