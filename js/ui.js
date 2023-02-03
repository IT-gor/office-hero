
let instruments = document.getElementsByClassName("select-instrument");
let markers = document.getElementsByClassName("select-marker");
let songs = document.getElementsByClassName("select-song");

let playButton = document.getElementById("playButton");
let play = false;

let marker = "marker_yellow";
let song = "ente";
var soundSource = "sounds/bell.wav";

instruments[0].classList.add('active')
markers[0].classList.add('active')
songs[0].classList.add('active')

toggle(instruments);
toggle(markers);
toggle(songs);

function toggle(array){
    for(let i=0;i<array.length;i++){
        let imgSource= "images/"+array[i].getAttribute('value');
        if(array[i].classList.contains('active')){
            array[i].style.backgroundImage = `url(${imgSource}_color.png)`;
        }
        
        array[i].addEventListener("mousedown", function(){
            if(array[i].classList.contains('instrument')){
                soundSource= "sounds/"+array[i].getAttribute('value')+".wav"
                //Instrument beim auswählen einmal in C5 abspielen
                loadSample(soundSource)
                .then(sample => {
                    const note = 72;
                    const velocity=120;
                    if (note) {
                        playSample(sample, note, velocity);
            }
        })
            }

            deToggleAll(array);
            array[i].classList.add('active');

            if(array[i].classList.contains('active')){
                array[i].style.backgroundImage = `url(${imgSource}_color.png)`;
            }

            if(array[i].hasAttribute('midi')){
                output = getOutput();
                output.send(JSON.parse(array[i].getAttribute('midi')));
            }

        });
        array[i].addEventListener("mouseover", function() {
            let imgSource= "images/"+array[i].getAttribute('value');
            array[i].style.backgroundImage = `url(${imgSource}_color.png)`;
        });
        array[i].addEventListener("mouseleave", function() {
            if(!array[i].classList.contains('active')){
                let imgSource= "images/"+array[i].getAttribute('value');
                array[i].style.backgroundImage = `url(${imgSource}.png)`;
            }
            
        });
    }
}

function deToggleAll(array){
    for(let i=0;i<array.length;i++){
        let imgSource= "images/"+array[i].getAttribute('value');
        array[i].classList.remove('active');
        array[i].style.backgroundImage = `url(${imgSource}.png)`;
    }
}
playButton.addEventListener('click',function(e){
    output = getOutput();

    console.log("EventListener: play: " + play)

    if(play){
        play=false;
        playButton.classList.remove('activeButton');
        playButton.innerHTML = "Play";
        output.send([177, 10, 10]);
    }
    else{
        play=true;
        playButton.classList.add('activeButton');
        playButton.innerHTML = "Stop";
        output.send([177, 10, 9]);
    }


});
