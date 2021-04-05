var eventBox = document.getElementById('event-box').textContent
var countdownBox = document.getElementById('countdown-box')

// console.log(eventBox);
var eventDate = Date.parse(eventBox)
// console(eventDate);

var myCountdown = setInterval(()=>{
    var now = new Date().getTime()
    //console.log(now)

    var diff = eventDate - now
    //console.log(diff)
    
    var d = Math.floor(eventDate / (1000 * 60 * 60 * 24) - (now / (1000 * 60 * 60 * 24)))
    var h = Math.floor((eventDate / (1000 * 60 * 60) - (now / (1000 * 60 * 60))) % 24)
    var m = Math.floor((eventDate / (1000 * 60) - (now / (1000 * 60))) % 60)
    var s = Math.floor((eventDate / (1000) - (now / (1000))) % 60)

    if (diff > 0) {
        countdownBox.innerHTML = d + " days, " + h + " hours, " + m + " minutes, " + s + " seconds"
    } else {
        clearInterval(myCountdown)
        countdownBox.innerHTML = "Auction Ended"
    }
}, 1000)
