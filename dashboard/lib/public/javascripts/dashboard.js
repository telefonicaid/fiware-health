function calc_height() {

    var D = document;
    console.log('doc.body:' + D.body + ' doc.docElem:' + D.documentElement);
    var height;
    if (is_chrome() || is_firefox()) {
        //chrome, FF
         height = Math.max(
            D.body.scrollHeight, D.documentElement.scrollHeight,
            D.body.offsetHeight, D.documentElement.offsetHeight,
            D.body.clientHeight, D.documentElement.clientHeight
        );

    } else {
        // safari
        console.log('safari');
        height = Math.max(
           D.documentElement.scrollHeight,
           D.documentElement.offsetHeight,
           D.documentElement.clientHeight
        );
    }

    console.log('resize to height: ' + height);
    window.parent.document.getElementById('iframe-container').style.height = height + 'px';

}

function displaySections() {

    console.log('displaySections');
    Array.prototype.forEach.call(document.querySelectorAll('h3, h4'), function (el) {
        el.addEventListener('click', function () {

            if (document.defaultView.getComputedStyle(el.nextElementSibling).display == 'none') {
                el.nextElementSibling.style.display = 'block';
            } else {
                el.nextElementSibling.style.display = 'none';
            }
            calc_height();

        });
    });
}


var strWindowFeatures = 'resizable=yes,scrollbars=yes,status=yes';
function openFailureDetailsInNewWindow(anchor_tag) {

    var html = document.getElementById('html_failure_details').innerHTML;

    if ( is_firefox()) {
        console.log('openFailureDetailsInNewWindow#firefox');

        window.parent.document.getElementById('iframe-container').contentDocument.body.innerHTML = html;
        window.parent.document.getElementById('iframe-container').contentWindow.location.hash = anchor_tag;
        displaySections();
        console.log('openFailureDetailsInNewWindow#calc');

    } else {
        if (is_chrome()) {
            console.log('openFailureDetailsInNewWindow#chrome_safari');

            var myWindow = window.open(anchor_tag, '_self', strWindowFeatures);


            var doc = myWindow.document;
            doc.open();
            doc.write(html);
            doc.close();
        } else {
            console.log('openFailureDetailsInNewWindow#safari ' + anchor_tag);

            window.parent.document.getElementById('iframe-container').contentDocument.body.innerHTML = html;
            window.parent.document.getElementById('iframe-container').contentWindow.location.hash = '#';

            displaySections();
            console.log('openFailureDetailsInNewWindow#calc');
        }


    }
    calc_height();

    console.log('openFailureDetailsInNewWindow#end');

}


function is_firefox() {
    return navigator.userAgent.toLowerCase().indexOf('firefox') > -1;
}

function is_chrome() {
    return navigator.userAgent.toLowerCase().indexOf('chrome') > -1;
}

function changeTitle(id) {
    var element = document.getElementById(id);
    var subtitle = element.innerText || element.textContent;
    var n = subtitle.search('.TestSuite');
    var underscore_position = subtitle.search('_');
    var new_subtitle = capitalizeFirstLetter(subtitle.substring(underscore_position + 1, n)) + subtitle.substring(n + 10);
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
    var value = 'waiting...';
    if (button.textContent == undefined) {
        button.innerText = value;
    } else {
        button.textContent = value;
    }

    window.open(region, '_self');
}



function loadReport(filename) {

  document.getElementById('box1').style.display = 'none';
  var el = document.getElementById('frameContainer');
  el.outerHTML = '<iframe id="iframe-container" src="' + filename + '" scrolling="no" style=""></iframe>';

}
