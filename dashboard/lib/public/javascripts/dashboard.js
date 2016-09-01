/*jslint browser: true*/
/*jshint unused:false*/

function isFirefox() {
    return navigator.userAgent.toLowerCase().indexOf('firefox') > -1;
}

function isChrome() {
    return navigator.userAgent.toLowerCase().indexOf('chrome') > -1;
}

function calcHeight() {

    var D = document;
    console.log('doc.body:' + D.body + ' doc.docElem:' + D.documentElement);
    var height;
    if (isChrome() || isFirefox()) {
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
    var iFrameContainer =  window.parent.document.getElementById('iframe-container');
    if (iFrameContainer !== null) {
        iFrameContainer.style.height = height + 'px';
    }

}

function displaySections() {

    console.log('displaySections');
    Array.prototype.forEach.call(document.querySelectorAll('h3, h4'), function (el) {
        el.addEventListener('click', function () {

            if (document.defaultView.getComputedStyle(el.nextElementSibling).display === 'none') {
                el.nextElementSibling.style.display = 'block';
            } else {
                el.nextElementSibling.style.display = 'none';
            }
            calcHeight();

        });
    });
}


var strWindowFeatures = 'resizable=yes,scrollbars=yes,status=yes';

function openFailureDetailsInNewWindow(anchorTag) {

    var html = document.getElementById('html_failure_details').innerHTML;
    var iFrameContainer =  window.parent.document.getElementById('iframe-container');

    if ( isFirefox()) {
        console.log('openFailureDetailsInNewWindow#firefox');

        if (iFrameContainer !== null) {
            iFrameContainer.contentDocument.body.innerHTML = html;
            iFrameContainer.contentWindow.location.hash = anchorTag;
        } else {
            document.getElementsByTagName('body')[0].innerHTML = html;
            document.location.hash = anchorTag;

        }

        displaySections();
        console.log('openFailureDetailsInNewWindow#calc');

    } else {
        if (isChrome()) {
            console.log('openFailureDetailsInNewWindow#chrome_safari');

            var myWindow = window.open(anchorTag, '_self', strWindowFeatures);


            var doc = myWindow.document;
            doc.open();
            doc.write(html);
            doc.close();
        } else {
            console.log('openFailureDetailsInNewWindow#safari ' + anchorTag);

            if (iFrameContainer !== null) {
                iFrameContainer.contentDocument.body.innerHTML = html;
                iFrameContainer.contentWindow.location.hash = '#';
            } else {
                document.getElementsByTagName('body')[0].innerHTML = html;
                document.location.hash = '#';
            }

            displaySections();
            console.log('openFailureDetailsInNewWindow#calc');
        }


    }
    calcHeight();

    console.log('openFailureDetailsInNewWindow#end');

}


function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}


function changeTitle(id) {
    var element = document.getElementById(id);
    var subtitle = element.innerText || element.textContent;
    var dotPosition = subtitle.search('\\.');
    var newSubtitle = capitalizeFirstLetter(subtitle.substring(dotPosition + 1));
    if (element.textContent === undefined) {
        document.getElementById(id).innerText = newSubtitle;
    } else {
        document.getElementById(id).textContent = newSubtitle;
    }

}

function changeAllTitles() {
    changeTitle('subtitle');
    changeTitle('subtitle2');
    changeTitle('subtitle3');
    changeTitle('subtitle4');
}


function refresh(button, region) {
    button.disabled = true;
    var value = 'waiting...';
    if (button.textContent === undefined) {
        button.innerText = value;
    } else {
        button.textContent = value;
    }

    window.open(region, '_self');
}



function loadReport(filename) {

  document.getElementById('box1').style.display = 'none';
  var el = document.getElementById('frameContainer');
  el.outerHTML = '<iframe id="iframe-container" src="' + filename +
      '" scrolling="no" style="padding-left: 40px;padding-right: 40px;"></iframe>';

}


function asyncLogout() {
    setTimeout(function() {
        Fiware.signOut('health'); // jshint ignore:line
    }, 0);
}

function logout(redirectUrl, logoutUrl) {
    console.log('after logout, go to: ' + redirectUrl);
    try {
        asyncLogout();
    } catch (err) {
        console.log('async logout: ' + err.message);
    }

    window.location.href = redirectUrl;
    return window.location.href;

}
