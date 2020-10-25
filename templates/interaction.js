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
