$(document).ready(function() {
  $('.js-example-basic-single').select2();
  $('.js-example-basic-multiple').select2();
  $('#roomTable').DataTable( {
    responsive: true,
    "pageLength": 5,
    rowReorder: {
      selector: 'td:nth-child(2)'
    }
  } );
  $('#rbookTable').DataTable( {
    responsive: true,
    "pageLength": 5,
    order: [[4, 'desc']],
    rowReorder: {
      selector: 'td:nth-child(2)'
    }
  } );
  $('#ebookTable').DataTable( {
    responsive: true,
    "pageLength": 5,
    order: [[4, 'desc']],
    rowReorder: {
      selector: 'td:nth-child(2)'
    }
  } );
  $('#regFacesTable').DataTable( {
    responsive: true,
    "pageLength": 5,
    order: [[4, 'desc']],
    rowReorder: {
      selector: 'td:nth-child(2)'
    }
  } );
  $('#RAccessLogTable').DataTable( {
    responsive: true,
    "pageLength": 5,
    order: [[4, 'desc']],
    rowReorder: {
      selector: 'td:nth-child(2)'
    }
  } );
  
  $('#reportsTable').DataTable( {
    responsive: true,
    "pageLength": 5,
    order: [[5, 'asc']],
    rowReorder: {
      selector: 'td:nth-child(2)'
    }
  } );

  $('.datepicker').datepicker({
    format: "mm-yyyy",
    startView: "months", 
    minViewMode: "months"
  });
});

function deleteAnnouncement(AnnounceId) {
    fetch("/delete-announcement", {
      method: "POST",
      body: JSON.stringify({ AnnounceId: AnnounceId }),
    }).then((_res) => {
      window.location.href = "/ManageAnnouncements";
    });
}

$('#rBookType').on('change',function(){
  var selection = $(this).val();
  switch(selection){
    case "student":
      $("#typeStudent").show()
      $("#typeStaff").hide()

      $("#typeStudent").prop('required', true);
      $("#typeStaff").prop('required', false);
      break;
    case "staff":
      $("#typeStaff").show()
      $("#typeStudent").hide()

      $("#typeStudent").prop('required', false);
      $("#typeStaff").prop('required', true);
      break;
    default:
      $("#otherType").hide()
      $("#otherType").hide()
  }
});

$('#eBookType').on('change',function(){
  var selection = $(this).val();
  switch(selection){
    case "student":
      $("#typeStudent").show()
      $("#typeStaff").hide()

      $("#typeStudent").prop('required', true);
      $("#typeStaff").prop('required', false);
      break;
    case "staff":
      $("#typeStaff").show()
      $("#typeStudent").hide()

      $("#typeStudent").prop('required', false);
      $("#typeStaff").prop('required', true);
      break;
    default:
      $("#otherType").hide()
      $("#otherType").hide()
  }
});

$('#feedbackType').on('change',function(){
  var selection = $(this).val();
  switch(selection){
    case "Room":
      $("#feedbackRBookType").show()
      $("#feedbackEBookType").hide()

      document.getElementById("feedbackRBookType").required = true;
      document.getElementById("feedbackEBookType").required = false;
      break;
    case "Event":
      $("#feedbackEBookType").show()
      $("#feedbackRBookType").hide()

      document.getElementById("feedbackEBookType").required = true;
      document.getElementById("feedbackRBookType").required = false;
      break;
    default:
      $("#otherType").hide()
      $("#otherType").hide()
  }
});

String.prototype.splice = function(idx, rem, str) {
  return this.slice(0, idx) + str + this.slice(idx + Math.abs(rem));
};


//Set default dates when booking without fullcalendar
var date = new Date();
var day = ("0" + date.getDate()).slice(-2);
var month = ("0" + (date.getMonth() + 1)).slice(-2);
var today = date.getFullYear() + "-" + (month) + "-" + (day);
$('#rbookstart').val(today);
$('#rbookend').val(today);
$('#ebookstart').val(today);
$('#ebookend').val(today);