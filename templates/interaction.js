function show(id) {
    document.getElementById(id).style.display = "block";
}
function hide(id) {
    document.getElementById(id).style.display = "none";
}

function showScrim() {
    document.body.classList.add("scrim");
}

function hideScrim() {
    document.body.classList.remove("scrim");
}

function showAbout() {
    showScrim();
    show("about");
}

function hideAbout() {
    hideScrim();
    hide("about");
}

function showSettings() {
    showScrim();
    show("settings");
}

function hideSettings() {
    hideScrim();
    hide("settings");
}

function showUpload() {
    showScrim();
    show("upload");
}

function hideUpload() {
    hideScrim();
    hide("upload");
}

function validateManySettings() {
    if (
        !document.many_settings.xy_symmetry.checked &&
        !document.many_settings.x_symmetry.checked &&
        !document.many_settings.y_symmetry.checked &&
        !document.many_settings.no_symmetry.checked
    ) {
        window.alert("You must choose some kind of symmetry!");
        return false;
    }
    return true;
}
