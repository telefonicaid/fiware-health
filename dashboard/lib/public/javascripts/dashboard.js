function calc_height() {
    var B = document.body,
    H = document.documentElement,
    height;

if (typeof document.height !== 'undefined') {
    height = document.height; // For webkit browsers
} else {
    height = Math.max( B.scrollHeight, B.offsetHeight,H.clientHeight, H.scrollHeight, H.offsetHeight );
}

    console.log("resize1 "+height);
    window.parent.document.getElementById('iframe-container').style.height = height + 'px';

}

function displaySections() {
    calc_height();

    Array.prototype.forEach.call(document.querySelectorAll('h3, h4'), function (el) {
        el.addEventListener('click', function () {

            if (document.defaultView.getComputedStyle(el.nextElementSibling).display == 'none') {
                el.nextElementSibling.style.display = 'block';
            } else {
                el.nextElementSibling.style.display = 'none';
            }
            calc_height();



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
    calc_height();
}

function changeTitle(id) {
    var element = document.getElementById(id);
    var subtitle = element.innerText || element.textContent;
    var n = subtitle.search(".TestSuite");
    var underscore_position = subtitle.search('_');
    var new_subtitle = capitalizeFirstLetter(subtitle.substring(underscore_position+1, n)) + subtitle.substring(n + 10);
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


function refresh(button, region) {
    button.disabled = true;
    var value = "waiting..";
    if (button.textContent == undefined) {
        button.innerText = value;
    } else {
        button.textContent = value;
    }

    window.open('/refresh?region=' + region, '_self');
}



function loadReport(filename) {

  document.getElementById("box1").style.display="none";
  var el=document.getElementById("frameContainer");
  el.outerHTML="<iframe id='iframe-container' src='/report/"+filename+"' scrolling='no'></iframe>";

}