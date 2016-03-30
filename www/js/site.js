$(document).ready(function() {
    var video = '<div class="video"><iframe width="800" height="450" src="https://www.youtube.com/embed/zL5_EsF06DM?rel=0&amp;showinfo=0&autoplay=1&start=624" frameborder="0" allowfullscreen></iframe></div>'
    $('img.hz-video, div.play-button').click(function() {
        $(this).parent().html(video);
    });
    $('form[name=hz-developer-preview]').validate({
        rules: { email: { email: true } },
        submitHandler: function(form) { form.submit(); }
    });
});
