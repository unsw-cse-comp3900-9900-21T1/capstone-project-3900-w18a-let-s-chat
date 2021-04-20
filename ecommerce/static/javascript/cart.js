<<<<<<< HEAD
var updateBtns = document.getElementsByClassName('update-cart')

for (i = 0; i < updateBtns.length; i++) {

	if (user == 'AnonymousUser'){
		document.getElementById('cart-icon').classList.add("hidden");
		document.getElementById('cart-total').classList.add("hidden");
		updateBtns[i].classList.add("hidden");
	}
	else {
		updateBtns[i].addEventListener('click', function(){
			var productId = this.dataset.product
			var action = this.dataset.action
			console.log('productId:', productId, 'Action:', action)
			console.log('USER:', user)
			if (user == 'AnonymousUser'){
				console.log('User is not authenticated')

				var url = "/login/"
				fetch(url, {
					method:'POST',
					headers:{
						'Content-Type':'application/json',
						'X-CSRFToken':csrftoken,
					}, 
					// body:JSON.stringify({'productId':productId, 'action':action})
				})
				.then((response) => {
				return response.json();
				})
				.then((data) => {
					console.log('data:',data)
					location.reload()
				});    

			}else{
				updateUserOrder(productId, action)
			}

		})
	}
}


function updateUserOrder(productId, action){
	console.log('User is authenticated, sending data...')

		var url = '/update_item/'

		fetch(url, {
			method:'POST',
			headers:{
				'Content-Type':'application/json',
				'X-CSRFToken':csrftoken,
			}, 
			body:JSON.stringify({'productId':productId, 'action':action})
		})
		.then((response) => {
		   return response.json();
		})
		.then((data) => {
            console.log('data:',data)
            location.reload()
		});
=======
var updateBtns = document.getElementsByClassName('update-cart')

for (i = 0; i < updateBtns.length; i++) {

	if (user == 'AnonymousUser'){
		document.getElementById('cart-icon').classList.add("hidden");
		document.getElementById('cart-total').classList.add("hidden");
		updateBtns[i].classList.add("hidden");
	}
	else {
		updateBtns[i].addEventListener('click', function(){
			var productId = this.dataset.product
			var action = this.dataset.action
			console.log('productId:', productId, 'Action:', action)
			console.log('USER:', user)
			if (user == 'AnonymousUser'){
				console.log('User is not authenticated')

				var url = "/login/"
				fetch(url, {
					method:'POST',
					headers:{
						'Content-Type':'application/json',
						'X-CSRFToken':csrftoken,
					}, 
					// body:JSON.stringify({'productId':productId, 'action':action})
				})
				.then((response) => {
				return response.json();
				})
				.then((data) => {
					console.log('data:',data)
					location.reload()
				});    

			}else{
				updateUserOrder(productId, action)
			}

		})
	}
}


function updateUserOrder(productId, action){
	console.log('User is authenticated, sending data...')

		var url = '/update_item/'

		fetch(url, {
			method:'POST',
			headers:{
				'Content-Type':'application/json',
				'X-CSRFToken':csrftoken,
			}, 
			body:JSON.stringify({'productId':productId, 'action':action})
		})
		.then((response) => {
		   return response.json();
		})
		.then((data) => {
            console.log('data:',data)
            location.reload()
		});
>>>>>>> Product_Searching
}