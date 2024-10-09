# SouthFeasts

# South Jakarta Flavors, SouthFeasts Delivers! 🍜🍖

## Anggota Kelompok B03
- [Gnade Yuka](https://github.com/yukaagnd) - 2306165704
- [Nabila Maharani Putri](https://github.com/nabsskrrtt) - 2306275191
- [Annisa Dwiyanti Ismael](https://github.com/annisadwiyanti) - 2306240111
- [Aliya Zahira Nadra](https://github.com/lollyyy) - 2306245863
- [Nasha Zahira](https://github.com/genshzin) - 2306165553

## Filosofi SouthFeasts:

SouthFeasts lahir dari kecintaan kami terhadap kekayaan kuliner Jakarta Selatan. Nama ini menggabungkan "South" yang merujuk pada Jakarta Selatan, dan "Feasts" yang berarti perjamuan atau perayaan makanan. SouthFeasts hadir sebagai pemandu digital yang mengajak pengguna untuk merayakan dan menjelajahi kelezatan kuliner di wilayah ini.

Jakarta Selatan, sebagai salah satu kawasan elit dan modern di Jakarta, menyimpan pesona kuliner yang tak kalah menarik. Di balik gedung-gedung pencakar langit dan pusat perbelanjaan mewah, tersembunyi berbagai hidden gems kuliner yang menawarkan cita rasa autentik hingga inovasi terbaru. Namun, informasi mengenai kekayaan kuliner Jakarta Selatan seringkali tersebar dan sulit diakses oleh wisatawan maupun penduduk lokal.

SouthFeasts hadir sebagai solusi untuk menjembatani kesenjangan informasi ini. Kami berkomitmen untuk menjadi platform yang memamerkan keberagaman kuliner Jakarta Selatan dan membantu wisatawan serta penduduk lokal untuk lebih mengenal dan menikmati beragam makanan yang ada di kota ini.

## Tujuan SouthFeasts
- Memperkenalkan kekayaan dan keberagaman kuliner Jakarta Selatan kepada wisatawan dan penduduk lokal.
- Menjadi sumber informasi terpercaya dan komprehensif tentang tempat makan di Jakarta Selatan.
- Memudahkan pengguna dalam menemukan dan menjelajahi cita rasa kota ini.
- Mendukung industri kuliner lokal dengan mempromosikan keunikan makanan Jakarta Selatan.
- Memperkaya pengalaman wisata kuliner di kota ini.


## 1. 🍽️ Filter, Dashboard Katalog Makanan dan Restoran (Admin View)
Dikerjakan oleh Nasha Zahira

Dashboard admin katalog makanan dan restoran ini memungkinkan Admin untuk memiliki akses penuh ke dashboard katalog makanan dan restoran. Admin dapat menambah, mengedit, atau menghapus entri makanan, serta melihat detail lengkap setiap makanan, seperti gambar, deskripsi, harga, lokasi, ulasan, dan rating. Fitur ini dirancang untuk mempermudah pengelolaan seluruh katalog dan menjaga informasi tetap akurat dan up-to-date. Kemudian juga ada filter untuk melakukan filter makanan berdasarkan preferensi. 

| Guest | Admin | Pengunjung (Traveller) |
|-------|--------------------------------|-------|
| - Tidak bisa mengakses dashboard admin | - Memiliki akses penuh untuk mengelola seluruh katalog. <br>- Dapat menambah, mengedit, atau menghapus entri makanan. <br>- Melihat detail lengkap setiap makanan (gambar, deskripsi, harga, lokasi, review dan rating) | - Tidak bisa mengakses dashboard admin |

## 2. ⭐ Wishlist
Dikerjakan oleh Aliya Zahira Nadra

Halaman wishlist hanya dapat diakses oleh pengunjung. Pada halaman ini, tampilan page nya akan berupa makanan-makanan yang sudah ditandai dengan sebuah icon. Page ini juga memiliki filter untuk mengorganisir data restoran yang ditandai berdasarkan kategori yang dibuat oleh pengunjung. Nama dari kategori ini tampilannya seperti collections yang isinya ditentukan sendiri oleh pengunjung.

Berikut aksi yang dapat dilakukan masing-masing role:

| Guest | Admin | Pengunjung (Traveller) |
|-------|--------------------------------|-------|
| - Tidak bisa mengakses wishlist. | - Tidak bisa mengakses wishlist. | - Mengakses halaman wishlist dan menyimpan makanan favoritnya. Membuat beberapa collections dalam page wishlist yang berisi kategori yang ditentukan oleh pengunjung. |

## 3. 📝 Review dan Rating Makanan
Dikerjakan oleh Gnade Yuka

Pengguna dapat memberikan ulasan dan rating untuk makanan yang telah mereka coba. Informasi ini ditampilkan di bawah katalog makanan dan juga pada halaman detail makanan.

Berikut aksi yang dapat dilakukan masing-masing role:

| Guest | Pengunjung (Traveler / Pembeli) | Admin |
|-------|--------------------------------|-------|
| - Dapat melihat review dan rating | - Dapat memberikan review dan rating<br>- Dapat mengedit atau menghapus review miliknya sendiri | - Memiliki semua akses Pengunjung<br>- Dapat memoderasi review (menghapus review yang tidak pantas)<br>- Dapat melihat statistik rating |

Contoh aksi:
- Guest: Membaca review tentang "Soto Betawi H. Mamat" untuk menilai kualitasnya.
- Pengunjung: Memberikan rating 4 bintang dan menulis review positif untuk "Nasi Uduk Kebon Kacang".
- Admin: Menghapus review yang mengandung kata-kata kasar pada "Mie Aceh Bang Jali".

## 4. 📰 Artikel Blog / QnA
Dikerjakan oleh Annisa Dwiyanti Ismael

Halaman khusus yang berisi artikel-artikel informatif tentang kuliner Jakarta Selatan serta fitur tanya jawab untuk pengguna.

Berikut aksi yang dapat dilakukan masing-masing role:

| Guest | Pengunjung (Traveler / Pembeli) | Admin |
|-------|--------------------------------|-------|
| - Dapat membaca artikel dan QnA | - Dapat membaca artikel dan QnA<br>- Dapat mengajukan pertanyaan di QnA<br>- Dapat memberikan komentar pada artikel | - Memiliki semua akses Pengunjung<br>- Dapat menulis dan mempublikasikan artikel baru<br>- Dapat menjawab pertanyaan di QnA<br>- Dapat mengelola (edit/hapus) konten artikel dan QnA |

Contoh aksi:
- Guest: Membaca artikel "5 Warung Sate Terenak di Tebet".
- Pengunjung: Mengajukan pertanyaan "Dimana bisa menemukan gudeg enak di Jakarta Selatan?" di forum QnA.
- Admin: Menulis dan mempublikasikan artikel baru berjudul "Panduan Kuliner Vegan di Jakarta Selatan".

## 5. 🏠 Halaman Restoran, Katalog Makanan, dan Filter
Dikerjakan oleh Nabila Maharani Putri

Ketika nama restoran diklik, pengguna akan diarahkan ke halaman khusus restoran tersebut yang menampilkan menu-menu yang tersedia (terbatas pada data yang ada dalam database). Fitur ini juga mencakup katalog makanan dan filter yang terintegrasi dengan modul Katalog Makanan dan Filter.

Berikut aksi yang dapat dilakukan masing-masing role:

| Guest | Pengunjung (Traveler / Pembeli) | Admin |
|-------|--------------------------------|-------|
| - Dapat melihat halaman restoran dan menu<br>- Dapat menggunakan filter pencarian | - Memiliki semua akses Guest<br>- Dapat memberikan rating dan review untuk restoran<br>- Dapat menambahkan menu ke wishlist | - Memiliki semua akses Pengunjung<br>- Dapat melakukan CRUD pada informasi restoran dan menu<br>- Dapat mengelola kategori restoran |

Contoh aksi:
- Guest: Melihat menu dan harga di halaman restoran "Sate Senayan".
- Pengunjung: Memberikan rating 5 bintang untuk restoran "Bakmi GM" setelah mencoba makannya.
- Admin: Menambahkan kategori baru "Restoran Ramah Anak" dan menambahkan beberapa restoran ke dalamnya.
