# DIMY: DID I MEET YOU

A contact tracing application

Introduction:

Contact tracing is an established technique that has proven successful in dealing with other outbreaks such as Ebola and SARS. Contact tracing aims to establish the close-contacts of an infected person so that they may be tested/isolated to break the chain of infection.

The application is intended to maintain clients interactions. We provide a method in which clients may stay anonymous and have little to no risk to their privacy. This is accomplished using sophisticated key exchanges, probabilistic storage, and decentralised systems. The report is presented in tasks so that the reader may easily follow along and have a complete grasp of the protocols. 

The application is based on the above paper. It propose a new privacy-preserving digital contact tracing protocol called ”Did I Meet You” (DIMY) that takes a holistic view of the privacy and security requirements for digital contact tracing and employ techniques to address most of the concerns associated with existing contact tracing protocols.

It makes the following specific contributions:
• DIMY has been designed to provide full life cycle data privacy protection that prevents contact tracing data from being used arbitrarily. This is achieved by using the Diffie-Hellman key exchange and a secret sharing mechanism, to establish a secret contact representation between user devices over an inherently insecure BLE broadcast channel. We also employ Bloom Filters for storing close contact information both at the individual device level as well as the back-end. Additionally, information from multiple close contacts are stored in a single fixed-size Bloom filter. This contact information is deleted from the user’s device once it is encoded in the Bloom filter, which serves two important purposes: (i) It prevents information leakage not only at the client level (for example as a result of device theft or coercion attacks), but also from authorities operating the backend and governments that can obtain subpoenas to access information stored on the back-end. (ii) It considerably reduces client device and back-end storage requirements.
• As opposed to traditional apps that employ centralised servers at the back-end, we have improved the scalability and security of our proposed solution by employing a blockchain-based back-end design in the ecosystem ( The application only stores a master bloom filter). This provides transparency and trust on back-end operations besides ensuring the integrity of data uploads from positively identified cases that are appended as blockchain transactions.