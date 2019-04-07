function sleep(milliseconds) {
  var start = new Date().getTime();
  for (var i = 0; i < 1e7; i++) {
    if ((new Date().getTime() - start) > milliseconds){
      break;
    }
  }
}

pcm_valid = false

function loader(argument) {
    '<div class="loader" style="margin:auto;"></div>'
}

function validate_pcm() {
    const params = new URLSearchParams(window.location.search)
    return $.ajax({
        type: 'get',
        data : params.toString(),
        url: 'ajax/complete_pcm_validate',
        success: function(data) {
            pcm_valid = data.success
        }})
}

function load_product_list(){
const params = new URLSearchParams(window.location.search)
return $.ajax({
    type: 'get',
    data : params.toString(),
    url: 'product-list-ajax',
    success: function(data) {
        $("#product-list-container").html(data)
    }})}

function meta_variables(){
    return $("meta#jsvars")[0].dataset
}

function slider_defaults(){
    obj = {
        type: "double",
        min: 0,
        // TODO: maximum price in whole db
        max: 200000,
        from: 200,
        to: 500,
        grid: true
    };
    for (key in meta_variables()){
        if (key.startsWith("default_slider_price")){
            id = key.slice(21)
            obj[id] = meta_variables()[key]
        }
    }
    obj.onFinish = function(data){
        change_get_params(
            {'minprice': data.from, 'maxprice': data.to}
        )
        load_product_list()
    }
    $(".js-range-slider").ionRangeSlider(obj)
}


function form_defaults() {
    for (key in meta_variables()){
        if (key.startsWith("default_")){
            id = key.slice(8)
            $("#" + id).each(function(){
                this.value = meta_variables()[key]
            })
        }
    }
}

$(document).ready(function(){
    ajax_call = load_product_list()
    $.when(ajax_call).done(function()
        {
            form_defaults()
            slider_defaults()
            // show first comparison
            show_one_more_comparison()
        })
})

function show_one_more_comparison() {
    $("div#comparisons .comparison[hidden=true]").first().attr('hidden', false);
}

function change_get_params(obj){
    params = new URLSearchParams(window.location.search)
    for (var key in obj){
        params.set(key, obj[key])
    }
    window.history.pushState({}, null, window.location.pathname + '?' + params.toString())
}

function empty_comparisons(){
    inputs_not_hidden = $(":not([hidden]).comparison input")
    var toReturn = false
    inputs_not_hidden.each(function()
        {
            if (this.value == ''){
                toReturn = true;
                return false;
            }
        }
    )
    return toReturn
}

$("#comparisons").submit(function (event)
    {
        event.preventDefault()
        filterData = $("#comparisons").serializeArray()
        obj = {}
        filterData.forEach(function(input){
            if (input.name!="csrfmiddlewaretoken"){
                obj[input.name] = input.value
            } 
        })
        change_get_params(obj)
        var success = true
        request = validate_pcm()
        $.when(request).done(
            function (){
                if ( pcm_valid ) {
                    load_product_list()
                } else if (!empty_comparisons()) {
                    show_one_more_comparison()
                }
            }
        )
    }
)

