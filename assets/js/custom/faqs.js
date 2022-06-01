$(document).ready(function(){
    $.getJSON("./assets/html/faqs.json", function(data){
        faqs_html=""
        for (category in data){
            faqs_html += `<div class="fs-5 fw-bold mb-2">${category}</div>
                <div class="accordion mb-4" id="${category.toLowerCase().replace(" ","-")}">`
            for (let i=0; i < data[category].length; i++){
                question_text = data[category][i]['question']
                answer_text = data[category][i]['answer']
                
                faqs_html += `<div class="accordion-item mb-3 shadow-sm">
                    <h2 class="accordion-header" id="${category.toLowerCase().replace(" ","-")}_heading${i}">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#${category.toLowerCase().replace(" ","-")}_collapse${i}" aria-expanded="false" aria-controls="${category.toLowerCase().replace(" ","-")}_collapse${i}">
                            ${question_text}
                        </button>
                    </h2>
                    <div id="${category.toLowerCase().replace(" ","-")}_collapse${i}" class="accordion-collapse collapse" aria-labelledby="${category.toLowerCase().replace(" ","-")}_heading${i}" data-bs-parent="#${category.toLowerCase().replace(" ","-")}">
                        <div class="accordion-body">
                            ${answer_text}
                        </div>
                    </div>
                </div>`
            }
            faqs_html += `</div>`
        }
        $("#faqs").html(faqs_html)
    }).fail(function(){
        console.log("An error has occurred.");
    });
});