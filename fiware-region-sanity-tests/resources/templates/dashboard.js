function displaySections() {
   Array.prototype.forEach.call(document.querySelectorAll('h1, h2, h3, h4'), function(el) {
        el.addEventListener('click', function() {
            el.nextElementSibling.style.display = document.defaultView.getComputedStyle(el.nextElementSibling).display == 'none' ? 'block' : 'none';
        })
    })
}

var strWindowFeatures = "resizable=yes,scrollbars=yes,status=yes";
function openFailureDetailsInNewWindow(){
    var html = document.getElementById("html_failure_details").innerHTML;
    var myWindow = window.open('','',strWindowFeatures);
    var doc = myWindow.document;
    doc.open();
    doc.write(html);
    doc.close();
}
