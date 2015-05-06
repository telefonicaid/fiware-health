function displaySections() {
    Array.prototype.forEach.call(document.querySelectorAll('h1, h2, h3, h4'), function (el) {
        el.addEventListener('click', function () {
            el.nextElementSibling.style.display = document.defaultView.getComputedStyle(el.nextElementSibling).display == 'none' ? 'block' : 'none';
        })
    })
}


var strWindowFeatures = "resizable=yes,scrollbars=yes,status=yes";
function openFailureDetailsInNewWindow(anchor_tag) {
    var html = document.getElementById("html_failure_details").innerHTML;
    var myWindow = window.open(anchor_tag, '_self', strWindowFeatures);
    var doc = myWindow.document;
    doc.open();
    doc.write(html);
    doc.close();
}

function changeTitle(id) {
    var element = document.getElementById(id);
    var subtitle = element.innerText || element.textContent;
    var n = subtitle.search(".TestSuite");
    var new_subtitle = "FIWARE Region " + capitalizeFirstLetter(subtitle.substring(33, n)) + subtitle.substring(n + 10);
    if (element.textContent == undefined) {
        document.getElementById(id).innerText = new_subtitle;
    } else {
        document.getElementById(id).textContent = new_subtitle;
    }

}

function changeAllTitles() {
    changeTitle('subtitle');
    changeTitle('subtitle2');

}

function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}
