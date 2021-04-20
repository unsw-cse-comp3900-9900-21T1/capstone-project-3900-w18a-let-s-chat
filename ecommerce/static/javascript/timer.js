var eventBox = document.getElementById('event-box').innerHTML
// var end_date = new Date(eventBox * 1000)
// console.log("end_date: " + end_date)
// console.log("eventBox: " + eventBox)
var countdownBox = document.getElementById('countdown-box')

// console.log(eventBox);
var eventDate = new Date(eventBox * 1000).getTime()
// var eventDate = end_date.getTime()
// console.log("eventdate: " + eventDate)

var myCountdown = setInterval(()=>{
    var now = new Date().getTime()
    // console.log("now: " + now)

    var diff = eventDate - now
    // console.log("diff: " + diff)
    
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
