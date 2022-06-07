$(document).ready(function(){
    $.getJSON("./assets/html/team.json", function(data){
        team_html=""
        for (let i=0; i < data.length; i++){
            member_item = data[i]
            member_name = member_item['name']
            member_bio = member_item['bio']
            member_image = member_item['image']
            
            team_html += `<div class="card row d-flex flex-row col-12 col-md-6 mb-3 offset-md-3">
                <div class="card-body p-0 col-sm-12 col-md-4 d-flex flex-column justify-content-center">
                    <div>
                        <img src="./assets/imgs/team/${member_image}">
                    </div>
                </div>
                <div class="card-body col-sm-12 col-md-8">
                    <p class="card-text">
                        <h5>${member_name}</h5>
                    </p>
                    <p class="card-text">
                        <span class="text-muted">
                            ${member_bio}
                        </span>
                    </p>
                </div>
            </div>`
        }
        $("#team").html(team_html)
    }).fail(function(){
        console.log("An error has occurred.");
    });
});