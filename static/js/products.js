function sleep(milliseconds) {
  var start = new Date().getTime();
  for (var i = 0; i < 1e7; i++) {
    if ((new Date().getTime() - start) > milliseconds){
      break;
    }
  }
}

pcm_valid = false
comparisonData = {}
defaultComparisonValue = 50
testVar = null
sliders = []

// config
compBackground = 'green'
comp2Background = 'blue'

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
    showProductListLoader()
    screenSizeData()
    const params = new URLSearchParams(window.location.search)
    return $.ajax({
        type: 'get',
        data : params.toString(),
        url: 'product-list-ajax',
        success: function(data) {
            $("#product-list").html(data)
            hideProductListLoader()
        }})
}

function load_full_product_list(){
const params = new URLSearchParams(window.location.search)
return $.ajax({
    type: 'get',
    data : params.toString(),
    url: 'ajax/all_products',
    success: function(data) {
        $("#product-list").html(data)
    }})}

function meta_variables(){
    return $("meta#jsvars")[0].dataset
}

function price_slider_init(){
    var obj = {
        type: "double",
        min: 0,
        step: 25000,
        // TODO: maximum price in whole db
        max: 250000,
        from: 25000,
        to: 100000,
        grid: true
    };
    // for (key in meta_variables()){
    //     if (key.startsWith("default_slider_price")){
    //         id = key.slice(21)
    //         obj[id] = meta_variables()[key]
    //     }
    // }
    obj.onFinish = function(data){
        change_get_params(
            {'minprice': data.from, 'maxprice': data.to}
        )
        load_product_list()
    }
    obj.onUpdate = obj.onFinish
    obj.onChange = function(data){
        $("#price-min-input").val(data.from)
        $("#price-max-input").val(data.to)
    }
    obj.onStart = async function(data){
        $("#price-min-input").change(
            function(){
                slider = $("#price-slider").data("ionRangeSlider")
                slider.update({
                    "from": this.value
                })})
        $("#price-max-input").change(
            function(){
                slider = $("#price-slider").data("ionRangeSlider")
                slider.update({
                    "to": this.value
                })})
        // once slider is ready, run onChange
        var bar = data.slider.children(':not(.custom_bar).irs-bar')
        while(!$("#price-slider").data().to){
            await new Promise(r=> setTimeout(r, 500))
        }
        obj.onChange($("#price-slider").data())
    }
    $("#price-slider").ionRangeSlider(obj)
}

function updatePriceGetData(){
    slider = $("#price-slider").data("ionRangeSlider")
    from = slider.old_from
    to = slider.old_to
    change_get_params(
        {'minprice': from, 'maxprice': to}
    )
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

function colored_criterion_names() {
    $('.comp_name1').css('color', compBackground)
    $('.comp_name2').css('color', comp2Background)
    
}

function screenSizeData(){
    var inputs = $('#screen-size-checkboxes input[type=checkbox]')
    var data = {}
    inputs.each(function(){
        data[this.name] = this.checked ? "1" : "0";
    })
    change_get_params(data)
}
$(document).ready(function(){
    ajax_call = load_product_list()
    url = new URL(window.location.href);
    // TODO no production!
    if (url.searchParams.get('test')) {
        load_full_product_list()
    }
    $(".checkbox").hover(
        function(){
            optionId = this.id.charAt(this.id.length-1)
            $("#img-screensize-default")[0].style.display = 'none';
            $("#img-screensize-" + optionId)[0].style.display = 'block';
        },
        function(){
            $("#img-screensize-" + optionId)[0].style.display = 'none';
            $("#img-screensize-default")[0].style.display = 'block';
        },
    )
    delete_get_params()
    $.when(ajax_call).done(function()
        {
            form_defaults()
            price_slider_init()
            colored_criterion_names()
            // show first comparison
            comparisonNext()
        })
    $("#screen-size-checkboxes input").change(function(){
        load_product_list()
    })
    hideMainLoader()
})

function loaderDo(which, operation){
    // which: either main or product-list
    // operation: show or hide
    // (str all)
    loader = $("#" + which + "-loader")[0]
    var container = $("#" + which + "-container")[0]
    if (operation == 'show'){
        container.style.display='none';
        loader.style.display='block';
    } else if (operation == 'hide'){
        loader.style.display='none';
        container.style.display='block';
    }
}


function hideMainLoader(){
    return loaderDo('main', 'hide')
}

function showMainLoader(){
    return loaderDo('main', 'show')
}

function showProductListLoader(){
    return loaderDo('product-list', 'show')
}
function hideProductListLoader(){
    return loaderDo('product-list', 'hide')
}

async function two_bar_slider(slider) {
    bar2 = slider.children('.custom_bar')
    alreadyExists = (bar2.length != 0)
    var bar = slider.children(':not(.custom_bar).irs-bar')
    if (!alreadyExists) {
        bar2 = bar.clone()
        bar2[0].classList.add('custom_bar')
        bar2[0].style.backgroundColor = comp2Background 
    } 
    // should wait until bar[0].style.left is not nan
    // if it is now
    while(!bar[0].style.left){
        await new Promise(r=> setTimeout(r, 500))
    }
    barLeftPercent = parseFloat(bar[0].style.left)
    barWidthPercent = parseFloat(bar[0].style.width)
    bar2WidthPercent = 100 - barWidthPercent
    bar2[0].style.left = barLeftPercent + barWidthPercent + '%'
    bar2[0].style.width = bar2WidthPercent - 2*barLeftPercent + '%' 
    if (!alreadyExists){
        bar2.insertAfter(bar)
    }
}

function setSliderColor(slider, color){
    bar = slider.children('span.irs-bar:not(.custom_bar)')
    bar[0].style.backgroundColor = color
    }

function indexOfActiveComparison(){
    comparisons = $("div.comparison")
    states = comparisons.map(function(){
        if (this.classList.contains('comparison-active')) {
            return true;
        } else {
            return false;
        }
    })
    return states.toArray().indexOf(true);
}

function idOfActiveComparison(){
    comparisons = $("div.comparison")
    index = indexOfActiveComparison()
    return comparisons[index].id.slice(7)
}

function checkIfComparisonFilled(comparisonId){
    return Boolean($("input#" + comparisonId).attr('set'))
}

function allComparisonIds(){
    return $("div.comparison").map(function(){
        return this.id.slice(7)
    }).toArray()
}

function checkIfCurrentComparisonFilled(comparisonId){
    return checkIfComparisonFilled(idOfActiveComparison())
}

function showOkButton(){
        $(".comp-ok-button").each(function(){
            this.classList.add('visible')
        })
}

function showOrHideOkButton(){
    if (pcm_valid){
        showOkButton()
    } else {
        $.when(validate_pcm()).done(function(){
            if (pcm_valid){
                showOkButton()
            }
        })
    }
}

function updateNotYets(){
    allComparisonIds().forEach(function(comparisonId){
        if (!checkIfComparisonFilled(comparisonId)){
            var display = 'block';
        } else {
            var display = 'none';
        }
        $("#"+comparisonId+"_notyetset")[0].style.display = display; 
    })
}

function showOrHideNavButtons() {
    var comparisons = $("div.comparison")
    var comp_num = comparisons.length
    var comparisonId = comparisons[indexOfActiveComparison()].id.slice(7)
    var notYetCompleted = !checkIfComparisonFilled(comparisonId)
    showOrHideOkButton()
    var last_comparison = (comp_num == indexOfActiveComparison()+1)
    updateNotYets()
    if (last_comparison || notYetCompleted){
        hideNextButton()
    } else {
        showNextButton()
    }
    if (indexOfActiveComparison() == 0){
        hideBackButton()
    } else {
        showBackButton()
    }
}

function switchActive(target, offset=false){
    // if offset is set, target will be ignored.
    activeIndex = indexOfActiveComparison()
    if (offset){
        target = activeIndex + offset
    }
    comparisons = $("div.comparison")
    comparisons.each(function(index){
        if (index == target){
            this.classList.add('comparison-active')
            this.classList.remove('comparison-hidden')
            initializeComparison(index)
        } else if (index == activeIndex) {
            this.classList.remove('comparison-active')
        }
    })
    showOrHideNavButtons()
    return true
}

function comparisonBack(){
    switchActive(false, -1)
    return false;
}

function comparisonNext(event){
    // validates the pcm and reloads
    // the product list if needed
    current_comparison = $(".comparison")[indexOfActiveComparison()]
    input = $(current_comparison).children('input.js-range-slider')
    switchActive(false, 1)
    updatePriceGetData()
    return false;
}

function initializeComparison(index) {
    var parent_elem = $("div.comparison")[index]
    var parent = $("#" + parent_elem.id)
    var comparison_id = parent_elem.id.slice(7)
    var input = parent.children(".comparison-slider")
    var obj = {
        type: "single",
        min: 1,
        // TODO: maximum price in whole db
        max: 99,
        from: 0,
        // from_fixed: true,
        from: defaultComparisonValue,
        grid: true,
        // skin: 'round'
    };
    obj.onFinish = function(data) {
        comparisonData[data.input.attr('id')] = data.from
        data.input.attr('set', true)
        // updateNotYets()
        comparisonsToUrl()
        showOrHideOkButton()
        showOrHideNavButtons()
    }
    obj.onChange = function(data){
        two_bar_slider(data.slider)
        span0 = data.input[0].id + '_0_percent'
        span1 = data.input[0].id + '_1_percent'
        $("span#"+span0).html(data.from)
        $("span#"+span1).html(100-data.from+"")
    }
    obj.onStart = function(data){
        $(document).ready(function(){
            setSliderColor(data.slider, compBackground)
            obj.onChange(data)
        })
    }
     sliders[comparison_id] = input.ionRangeSlider(obj)
}

function delete_get_params(obj){
    window.history.pushState({}, null, window.location.pathname)
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

function empty_comparisons() {
    // TODO either remove this or make this have some function
    return false;
}

function sliderData() {
    return comparisonData
}

function comparisonsToUrl(){
    filterData = $("#comparisons").serializeArray()
    obj = sliderData()
    change_get_params(obj)
}

function comparisonSubmit(){
    var success = true
    request = validate_pcm()
    $.when(request).done(
        function (){
            if ( pcm_valid ) {
                load_product_list()
            }
        }
    )
    return request
}

function showBackButton(){
    $(".comp-back-button").each(function(){
        this.classList.add('visible')   })
}

function hideBackButton(){
    $(".comp-back-button").each(function(){
        this.classList.remove('visible')
    })
}
function hideNextButton(){
    $(".comp-next-button").each(function(){
        this.classList.remove('visible')
    })
}
function showNextButton(){
    $(".comp-next-button").each(function(){
        this.classList.add('visible')
    })
}
// TODO rem?
$("#comparisons").submit(function (event)
    {
        event.preventDefault()
        // comparisonSubmit()
    }
)

