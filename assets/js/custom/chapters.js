$(document).ready(function(){
    $.getJSON("./assets/html/chapters.json", function(data){
        chapters_html=""
        for (let i=0; i < data.length; i++){
            theme = data[i]
            theme_number = theme[0]
            theme_topic = theme[1]
            theme_html = `<div class="row p-0 mx-0 mx-md-auto accordion-item justify-content-center mb-3 col-12 col-md-10 offset-md-1 theme-container">
                <h2 class="accordion-header p-0" id="chapters_heading${i}">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#chapters_collapse${i}" aria-expanded="false" aria-controls="chapters_collapse${i}">
                        <div class="theme-title fs-3"><span class="number fw-bold">${theme_number}.</span>${theme_topic}</div>
                    </button>
                </h2>
                <div id="chapters_collapse${i}" class="accordion-collapse collapse" aria-labelledby="chapters_heading${i}">
                    <div class='row p-2'>`
            for (let j=0; j < theme[2].length; j++){
                level_item = theme[2][j]
                theme_html += `<div class="col-12 col-md-4 topic mb-3 mb-md-0 d-flex align-items-stretch" style="max-width:400px">
                    <div class="card shadow-sm p-3 flex-column">
                        <div class="d-flex">
                            <div class="level-tag ${level_item['level']} text-capitalize mb-2 fw-bold text-white">${level_item['level']}</div><br>
                        </div>
                        <div class="d-flex fs-5 mb-4">
                            ${level_item["topic-title"]}
                        </div>`
                
                if ("notebook-link" in level_item){
                    if (level_item["notebook-link"] == "#"){
                        theme_html += `<div class="d-flex flex-row-reverse fs-5 mb-0 link inactive">
                            <a href="#!" class="text-reset">Coming Soon...</a>
                        </div>`
                    } else {
                        theme_html += `<div class="d-flex flex-row-reverse fs-5 mb-0 link colab">
                            <a href="${level_item["notebook-link"].replace("github.com","githubtocolab.com")}" target="_blank" class="text-reset"><img src="./assets/icons/colab-icon.png" class="d-inline-block">Go to Notebook</a>
                        </div>`
                    }   
                }

                if ("youtube-link" in level_item && level_item["youtube-link"] != "#"){
                    theme_html += `<div class="d-flex flex-row-reverse fs-5 mb-0 link youtube">
                        <a href="${level_item["youtube-link"]}" target="_blank" class="text-reset"><img src="./assets/icons/youtube-icon.png" class="d-inline-block">Watch the Video</a>
                    </div>`
                }

                theme_html += `</div>
                </div>`
            }
            theme_html += `</div>
                    </div>
                </div>
            </div>`
            chapters_html += theme_html
        }
        $("#chapters").html(chapters_html)
    }).fail(function(){
        console.log("An error has occurred.");
    });
});