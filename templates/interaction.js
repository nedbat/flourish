function show(id) {
    document.getElementById(id).style.display = "block";
}
function hide(id) {
    document.getElementById(id).style.display = "none";
}

function showAbout() {
    show("scrim");
    show("about");
}

function hideAbout() {
    hide("scrim");
    hide("about");
}

function showSettings() {
    show("scrim");
    show("settings");
}

function hideSettings() {
    hide("scrim");
    hide("settings");
}
